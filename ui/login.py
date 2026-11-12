from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QCheckBox, QFrame
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap

import theme
from database import users


class LoginPage(QWidget):
    login_ok = Signal(int, str)
    go_to_register = Signal()

    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hero = QFrame()
        hero.setObjectName("LoginHero")
        hero.setStyleSheet(f"#LoginHero {{ background-color: {theme.ACCENT_2}; }}")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(40, 50, 40, 40)
        hero_layout.setSpacing(6)
        hero_layout.setAlignment(Qt.AlignTop)

        heart = QLabel("♥")
        heart.setStyleSheet("color: white; font-size: 34px;")
        hero_layout.addWidget(heart)

        title = QLabel("Cardiac")
        title.setStyleSheet("color: white; font-size: 26px; font-weight: 700;")
        hero_layout.addWidget(title)

        subtitle = QLabel("Rhythm Analysis System")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px;")
        hero_layout.addWidget(subtitle)

        rule = QFrame()
        rule.setFixedSize(40, 3)
        rule.setStyleSheet("background-color: white;")
        hero_layout.addSpacing(8)
        hero_layout.addWidget(rule)
        hero_layout.addSpacing(8)

        tagline = QLabel("Clinical ECG analysis and reporting in one focused workspace.")
        tagline.setWordWrap(True)
        tagline.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 12px;")
        hero_layout.addWidget(tagline)
        hero_layout.addStretch()

        pulse_img = QLabel()
        pixmap = QPixmap(theme.icon("pulse_hero"))
        if not pixmap.isNull():
            pulse_img.setPixmap(pixmap.scaledToWidth(320, Qt.SmoothTransformation))
        hero_layout.addWidget(pulse_img)

        outer.addWidget(hero, stretch=4)

        form_wrap = QWidget()
        form_outer = QVBoxLayout(form_wrap)
        form_outer.setAlignment(Qt.AlignVCenter)
        form_outer.setContentsMargins(45, 40, 45, 40)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        title2 = QLabel("Welcome back")
        title2.setStyleSheet(f"color: {theme.TEXT}; font-size: 22px; font-weight: 700;")
        layout.addWidget(title2)
        subtitle2 = QLabel("Sign in to continue")
        subtitle2.setObjectName("PageSubtitle")
        layout.addWidget(subtitle2)
        layout.addSpacing(18)

        layout.addWidget(self._label("USERNAME"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. dr.mehta")
        layout.addWidget(self.username_input)

        layout.addWidget(self._label("PASSWORD"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.returnPressed.connect(self.try_login)
        layout.addWidget(self.password_input)

        self.remember_check = QCheckBox("Remember me")
        self.remember_check.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        layout.addWidget(self.remember_check)

        layout.addSpacing(12)
        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("PrimaryButton")
        login_btn.clicked.connect(self.try_login)
        layout.addWidget(login_btn)

        row = QHBoxLayout()
        row.addStretch()
        hint = QLabel("Don't have an account?")
        hint.setStyleSheet(f"color: {theme.MUTED}; font-size: 12px;")
        row.addWidget(hint)
        create_btn = QPushButton("Create one")
        create_btn.setFlat(True)
        create_btn.setStyleSheet(f"background: transparent; border: none; color: {theme.ACCENT}; font-size: 12px;")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self.go_to_register.emit)
        row.addWidget(create_btn)
        row.addStretch()
        layout.addLayout(row)

        form_outer.addLayout(layout)
        outer.addWidget(form_wrap, stretch=5)

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("StatLabel")
        return label

    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing info", "Enter both username and password.")
            return

        try:
            user = users.verify_login(username, password)
        except Exception as exc:
            QMessageBox.critical(self, "Database error", f"Could not reach the database:\n{exc}")
            return

        if not user:
            QMessageBox.warning(self, "Login failed", "Incorrect username or password.")
            return

        display_name = user["full_name"] or user["username"]
        self.password_input.clear()
        self.login_ok.emit(user["id"], display_name)
