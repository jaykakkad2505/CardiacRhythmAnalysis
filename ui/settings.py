import os
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QFileDialog, QLineEdit, QDialog, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

import theme
from database import users
from database.connection import get_connection
from config import DB_CONFIG


class SettingsPage(QWidget):
    logout_requested = Signal()
    profile_updated = Signal(str)

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 26, 36, 26)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Manage your workspace, data, and account.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        row = QHBoxLayout()
        row.setSpacing(16)

        # --- Appearance ---
        appearance_card = self._section_card("Appearance", "Customize the look and feel of the application.", "🖌", "#EF4444")
        al = appearance_card.layout()
        appearance_row = QHBoxLayout()
        appearance_row.addWidget(QLabel("Dark mode"))
        appearance_row.addStretch()
        self.dark_mode_toggle = QCheckBox()
        self.dark_mode_toggle.setChecked(True)
        self.dark_mode_toggle.setEnabled(False)
        self.dark_mode_toggle.setToolTip("A light theme is on the roadmap - see Future Scope.")
        self.dark_mode_toggle.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 34px; height: 18px; border-radius: 9px; background-color: {theme.ACCENT}; }}
            QCheckBox::indicator:checked {{ background-color: {theme.ACCENT}; }}
        """)
        appearance_row.addWidget(self.dark_mode_toggle)
        al.addLayout(appearance_row)
        al.addWidget(self._muted("A light theme is on the roadmap - see Future Scope."))
        al.addStretch()
        row.addWidget(appearance_card, stretch=1)

        # --- Data & backup ---
        data_card = self._section_card("Data & Backup", "Backup, restore, and export your database.", "🗄", "#3B82F6")
        dl = data_card.layout()
        backup_btn = QPushButton("⬆  Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        dl.addWidget(backup_btn)
        export_btn = QPushButton("⬇  Export Database to File")
        export_btn.clicked.connect(self.export_database)
        dl.addWidget(export_btn)
        dl.addStretch()
        row.addWidget(data_card, stretch=1)

        # --- Account ---
        account_card = self._section_card("Account", "View your account details and manage your session.", "👤", "#22C55E")
        acl = account_card.layout()

        self.name_display = QLabel("")
        self.name_display.setStyleSheet(f"color: {theme.TEXT}; font-size: 14px; font-weight: 600;")
        acl.addWidget(self.name_display)
        self.username_display = QLabel("")
        self.username_display.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        acl.addWidget(self.username_display)
        acl.addSpacing(10)

        edit_name_btn = QPushButton("Edit Display Name")
        edit_name_btn.clicked.connect(self.edit_name)
        acl.addWidget(edit_name_btn)

        change_pw_btn = QPushButton("Change Password")
        change_pw_btn.clicked.connect(self.change_password)
        acl.addWidget(change_pw_btn)

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("DangerButton")
        logout_btn.clicked.connect(self.confirm_logout)
        acl.addWidget(logout_btn)
        acl.addStretch()
        row.addWidget(account_card, stretch=1)

        layout.addLayout(row)
        layout.addStretch()

    def _section_card(self, title_text, subtitle_text, icon_char="", icon_color=None):
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        header_row = QHBoxLayout()
        if icon_char:
            badge = QLabel(icon_char)
            badge.setFixedSize(30, 30)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(f"background-color: {theme.SURFACE_2}; color: {icon_color or theme.ACCENT}; border-radius: 6px; font-size: 14px;")
            header_row.addWidget(badge)
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {theme.TEXT}; font-size: 14px; font-weight: 700;")
        header_row.addWidget(title)
        header_row.addStretch()
        card_layout.addLayout(header_row)

        subtitle = QLabel(subtitle_text)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        card_layout.addWidget(subtitle)
        return card

    def _muted(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px; font-style: italic;")
        return label

    def refresh(self):
        if not self.session.doctor_id:
            return
        user = users.get_user_by_id(self.session.doctor_id)
        if not user:
            return
        self.name_display.setText(user["full_name"] or user["username"])
        self.username_display.setText(f"@{user['username']}")

    def edit_name(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Display Name")
        dialog.resize(320, 130)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Full name:"))
        name_input = QLineEdit(self.name_display.text())
        layout.addWidget(name_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_name = name_input.text().strip()
            if new_name:
                users.update_profile(self.session.doctor_id, new_name)
                self.session.doctor_name = new_name
                self.refresh()
                self.profile_updated.emit(new_name)

    def change_password(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Password")
        dialog.resize(320, 220)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Current password:"))
        current_input = QLineEdit()
        current_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(current_input)

        layout.addWidget(QLabel("New password:"))
        new_input = QLineEdit()
        new_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(new_input)

        layout.addWidget(QLabel("Confirm new password:"))
        confirm_input = QLineEdit()
        confirm_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(confirm_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        current, new, confirm = current_input.text(), new_input.text(), confirm_input.text()
        if not current or not new:
            QMessageBox.warning(self, "Missing info", "Fill in all password fields.")
            return
        if len(new) < 4:
            QMessageBox.warning(self, "Weak password", "New password must be at least 4 characters.")
            return
        if new != confirm:
            QMessageBox.warning(self, "Mismatch", "New passwords do not match.")
            return

        if users.change_password(self.session.doctor_id, current, new):
            QMessageBox.information(self, "Password updated", "Your password has been changed.")
        else:
            QMessageBox.warning(self, "Incorrect password", "Your current password was incorrect.")

    def backup_database(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", f"cardiac_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.sql", "SQL Files (*.sql)"
        )
        if not path:
            return
        try:
            self._dump_database(path)
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        QMessageBox.information(self, "Backup complete", f"Database backed up to:\n{path}")

    def export_database(self):
        self.backup_database()

    def _dump_database(self, path):
        """Simple logical backup: dumps every table's rows as INSERT
        statements, since mysqldump may not be available on every machine."""
        conn = get_connection()
        try:
            with conn.cursor() as cur, open(path, "w") as f:
                f.write(f"-- Cardiac Rhythm Analysis System backup\n-- {datetime.now()}\n\n")
                for table in ["users", "patients", "ecg_reports", "report_history"]:
                    cur.execute(f"SELECT * FROM {table}")
                    rows = cur.fetchall()
                    for row in rows:
                        cols = ", ".join(row.keys())
                        vals = ", ".join(
                            "NULL" if v is None else f"'{str(v).replace(chr(39), chr(39)+chr(39))}'"
                            for v in row.values()
                        )
                        f.write(f"INSERT INTO {table} ({cols}) VALUES ({vals});\n")
        finally:
            conn.close()

    def confirm_logout(self):
        reply = QMessageBox.question(
            self, "Log out of Cardiac?", "You will need to sign in again to continue."
        )
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()
