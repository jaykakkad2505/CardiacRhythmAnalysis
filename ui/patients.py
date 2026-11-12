from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

import theme
from database import patients as patients_db
from database import reports as reports_db


class PatientFormDialog(QDialog):
    """Modal Add/Edit Patient form, matching the mockup's "Add Patient" button
    opening a dialog rather than an inline form taking up page space."""

    def __init__(self, parent=None, patient_row=None):
        super().__init__(parent)
        self.patient_row = patient_row
        self.setWindowTitle("Edit Patient" if patient_row else "Add Patient")
        self.resize(380, 340)
        self.build_ui()
        if patient_row:
            self._prefill(patient_row)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(self._label("NAME"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Aisha Patel")
        layout.addWidget(self.name_input)

        row = QHBoxLayout()
        age_col = QVBoxLayout()
        age_col.addWidget(self._label("AGE"))
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("e.g. 34")
        age_col.addWidget(self.age_input)
        row.addLayout(age_col)

        gender_col = QVBoxLayout()
        gender_col.addWidget(self._label("GENDER"))
        self.gender_input = QComboBox()
        self.gender_input.addItems(["", "Male", "Female", "Other"])
        gender_col.addWidget(self.gender_input)
        row.addLayout(gender_col)
        layout.addLayout(row)

        layout.addWidget(self._label("CONTACT (OPTIONAL)"))
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Phone or email")
        layout.addWidget(self.contact_input)

        layout.addWidget(self._label("NOTES (OPTIONAL)"))
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Known conditions, history, etc.")
        layout.addWidget(self.notes_input)

        layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("StatLabel")
        return label

    def _prefill(self, row):
        self.name_input.setText(row["name"])
        self.age_input.setText(str(row["age"]) if row["age"] else "")
        idx = self.gender_input.findText(row["gender"] or "")
        self.gender_input.setCurrentIndex(idx if idx >= 0 else 0)
        self.contact_input.setText(row["contact"] or "")
        self.notes_input.setText(row["notes"] or "")

    def get_values(self):
        age_text = self.age_input.text().strip()
        return {
            "name": self.name_input.text().strip(),
            "age": int(age_text) if age_text.isdigit() else None,
            "gender": self.gender_input.currentText(),
            "contact": self.contact_input.text().strip(),
            "notes": self.notes_input.text().strip(),
        }


class PatientsPage(QWidget):
    patients_changed = Signal()
    start_ecg_requested = Signal(str)  # patient name

    def __init__(self):
        super().__init__()
        self.selected_patient = None
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 26, 36, 26)
        layout.setSpacing(14)

        title = QLabel("Patient Management")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Add, update, search, and delete patient records - the demographic context every ECG recording is attached to.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or patient ID...")
        self.search_input.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_input, stretch=2)

        self.gender_filter = QComboBox()
        self.gender_filter.addItems(["All Genders", "Male", "Female", "Other"])
        self.gender_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.gender_filter, stretch=1)

        add_btn = QPushButton("+ Add Patient")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self.open_add_dialog)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        table_col = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Patient ID", "Name", "Age", "Gender", "Contact", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().resizeSection(5, 160)
        self.table.horizontalHeader().resizeSection(4, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        table_col.addWidget(self.table, stretch=1)

        self.pagination_label = QLabel("")
        self.pagination_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        self.pagination_label.setAlignment(Qt.AlignRight)
        table_col.addWidget(self.pagination_label)

        content_row.addLayout(table_col, stretch=2)

        self.detail_card = QFrame()
        self.detail_card.setObjectName("Card")
        self.detail_card.setFixedWidth(300)
        self.detail_layout = QVBoxLayout(self.detail_card)
        self.detail_layout.setContentsMargins(20, 20, 20, 20)
        self.detail_layout.setSpacing(6)
        self.detail_layout.setAlignment(Qt.AlignTop)
        self._render_empty_detail()
        content_row.addWidget(self.detail_card, stretch=1)

        layout.addLayout(content_row, stretch=1)

    def _render_empty_detail(self):
        self._clear_layout(self.detail_layout)
        placeholder = QLabel("Select a patient to view their details here.")
        placeholder.setObjectName("PageSubtitle")
        placeholder.setWordWrap(True)
        self.detail_layout.addWidget(placeholder)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def open_add_dialog(self):
        dialog = PatientFormDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.get_values()
        if not values["name"]:
            QMessageBox.warning(self, "Missing info", "Please enter a patient name.")
            return
        if patients_db.patient_name_exists(values["name"]):
            QMessageBox.warning(self, "Already exists", "A patient with this name already exists.")
            return
        try:
            patients_db.add_patient(values["name"], values["age"], values["gender"], values["contact"], values["notes"])
        except Exception as exc:
            QMessageBox.critical(self, "Database error", str(exc))
            return
        self.refresh()
        self.patients_changed.emit()

    def open_edit_dialog(self, patient_row):
        dialog = PatientFormDialog(self, patient_row)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.get_values()
        if not values["name"]:
            QMessageBox.warning(self, "Missing info", "Please enter a patient name.")
            return
        try:
            patients_db.update_patient(
                patient_row["id"], values["name"], values["age"], values["gender"],
                values["contact"], values["notes"],
            )
        except Exception as exc:
            QMessageBox.critical(self, "Database error", str(exc))
            return
        self.refresh()
        self.patients_changed.emit()
        if self.selected_patient and self.selected_patient["id"] == patient_row["id"]:
            self.selected_patient = patients_db.get_patient_by_id(patient_row["id"])
            self._render_detail(self.selected_patient)

    def confirm_delete(self, patient_row):
        reply = QMessageBox.question(
            self, "Delete Patient",
            f"Delete {patient_row['name']}? Their ECG reports will also be removed.",
        )
        if reply == QMessageBox.Yes:
            patients_db.delete_patient(patient_row["id"])
            if self.selected_patient and self.selected_patient["id"] == patient_row["id"]:
                self.selected_patient = None
                self._render_empty_detail()
            self.refresh()
            self.patients_changed.emit()

    def select_patient(self, patient_row):
        self.selected_patient = patient_row
        self._render_detail(patient_row)

    def _render_detail(self, patient):
        self._clear_layout(self.detail_layout)

        avatar = QLabel("👤")
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"background-color: {theme.ACCENT_2}; border-radius: 28px; font-size: 22px;")
        self.detail_layout.addWidget(avatar)

        name_label = QLabel(patient["name"])
        name_label.setStyleSheet(f"color: {theme.TEXT}; font-size: 16px; font-weight: 700;")
        self.detail_layout.addWidget(name_label)

        id_label = QLabel(patient["patient_code"])
        id_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        self.detail_layout.addWidget(id_label)
        self.detail_layout.addSpacing(10)

        info_title = QLabel("PERSONAL INFORMATION")
        info_title.setObjectName("StatLabel")
        self.detail_layout.addWidget(info_title)

        for label, value in [
            ("Age", str(patient["age"]) if patient["age"] else "-"),
            ("Gender", patient["gender"] or "-"),
            ("Contact", patient["contact"] or "-"),
        ]:
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
            v = QLabel(value)
            v.setStyleSheet(f"color: {theme.TEXT}; font-size: 11px;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            self.detail_layout.addLayout(row)

        self.detail_layout.addSpacing(10)
        vital_title = QLabel("LATEST VITAL")
        vital_title.setObjectName("StatLabel")
        self.detail_layout.addWidget(vital_title)

        latest_reports = reports_db.get_reports_for_patient(patient["id"])
        vital_card = QFrame()
        vital_card.setStyleSheet(f"background-color: {theme.SURFACE_2}; border-radius: 4px;")
        vital_layout = QVBoxLayout(vital_card)
        vital_layout.setContentsMargins(10, 8, 10, 8)
        if latest_reports:
            latest = latest_reports[0]
            hr_text = f"{latest['heart_rate']} BPM" if latest["heart_rate"] else "-"
            hr_label = QLabel(hr_text)
            hr_label.setStyleSheet(f"color: {theme.GOOD if latest['status']=='Stable' else theme.WARN}; font-size: 15px; font-weight: 700;")
            vital_layout.addWidget(hr_label)
            date_label = QLabel(str(latest["created_at"]))
            date_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
            vital_layout.addWidget(date_label)
        else:
            no_data = QLabel("No ECG recordings yet.")
            no_data.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
            vital_layout.addWidget(no_data)
        self.detail_layout.addWidget(vital_card)

        self.detail_layout.addSpacing(10)
        notes_title = QLabel("NOTES")
        notes_title.setObjectName("StatLabel")
        self.detail_layout.addWidget(notes_title)
        notes_label = QLabel(patient["notes"] or "No notes available.")
        notes_label.setWordWrap(True)
        notes_label.setStyleSheet(f"color: {theme.TEXT}; font-size: 11px;")
        self.detail_layout.addWidget(notes_label)

        self.detail_layout.addSpacing(14)
        edit_btn = QPushButton("Edit Patient")
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(patient))
        self.detail_layout.addWidget(edit_btn)

        start_ecg_btn = QPushButton("Start ECG Analysis")
        start_ecg_btn.setObjectName("PrimaryButton")
        start_ecg_btn.clicked.connect(lambda: self.start_ecg_requested.emit(patient["name"]))
        self.detail_layout.addWidget(start_ecg_btn)

        self.detail_layout.addStretch()

    def refresh(self):
        term = self.search_input.text().strip()
        rows = patients_db.search_patients(term) if term else patients_db.get_all_patients()

        gender = self.gender_filter.currentText()
        if gender != "All Genders":
            rows = [r for r in rows if r["gender"] == gender]

        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["patient_code"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(row["age"]) if row["age"] else ""))
            self.table.setItem(r, 3, QTableWidgetItem(row["gender"] or ""))
            self.table.setItem(r, 4, QTableWidgetItem(row["contact"] or ""))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(6)
            view_btn = QPushButton("View")
            view_btn.setFixedHeight(26)
            view_btn.setMinimumWidth(56)
            view_btn.clicked.connect(lambda checked=False, r=row: self.select_patient(r))
            action_layout.addWidget(view_btn)
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("DangerButton")
            delete_btn.setFixedHeight(26)
            delete_btn.setMinimumWidth(72)
            delete_btn.clicked.connect(lambda checked=False, r=row: self.confirm_delete(r))
            action_layout.addWidget(delete_btn)
            self.table.setCellWidget(r, 5, action_widget)

        self.pagination_label.setText(f"Showing {len(rows)} of {len(patients_db.get_all_patients())} patients")
