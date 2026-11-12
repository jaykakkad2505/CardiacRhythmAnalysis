import os

import numpy as np
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QFileDialog, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal

from database import patients as patients_db


class ImportEcgPage(QWidget):
    dataset_ready = Signal()  # session.signal / session.patient_id are set; safe to go to Analysis

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)

        title = QLabel("Import ECG Dataset")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Select a patient and upload a CSV/TXT/XLSX waveform file; the app validates it before analysis.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("Card")
        form = QVBoxLayout(card)
        form.setContentsMargins(24, 22, 24, 22)
        form.setSpacing(14)

        form.addWidget(self._label("SELECTED PATIENT"))
        self.patient_selector = QComboBox()
        form.addWidget(self.patient_selector)

        row = QHBoxLayout()
        rate_col = QVBoxLayout()
        rate_col.addWidget(self._label("SAMPLING RATE (Hz)"))
        self.rate_input = QLineEdit("250")
        self.rate_input.setFixedWidth(120)
        rate_col.addWidget(self.rate_input)
        row.addLayout(rate_col)
        row.addStretch()
        form.addLayout(row)

        form.addWidget(self._label("DATASET FILE"))
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #6b7280;")
        form.addWidget(self.file_label)

        browse_btn = QPushButton("  Drop / Browse for ECG File (.csv .txt .xlsx)")
        browse_btn.setObjectName("PrimaryButton")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_file)
        form.addWidget(browse_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        form.addWidget(self.status_label)

        next_row = QHBoxLayout()
        next_row.addStretch()
        self.next_btn = QPushButton("Continue to Analysis  →")
        self.next_btn.setObjectName("PrimaryButton")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.continue_to_analysis)
        next_row.addWidget(self.next_btn)
        form.addLayout(next_row)

        layout.addWidget(card)
        layout.addStretch()

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("StatLabel")
        return label

    def reload_patient_list(self):
        current = self.patient_selector.currentText()
        self.patient_selector.blockSignals(True)
        self.patient_selector.clear()
        rows = patients_db.get_all_patients()
        self._patients_by_name = {p["name"]: p for p in rows}
        self.patient_selector.addItems([p["name"] for p in rows])
        if current in self._patients_by_name:
            self.patient_selector.setCurrentText(current)
        self.patient_selector.blockSignals(False)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select ECG Dataset", "", "ECG Data Files (*.csv *.txt *.xlsx *.xls);;All Files (*)"
        )
        if not path:
            return

        try:
            signal = self._load_signal(path)
        except Exception as exc:
            QMessageBox.critical(self, "Could not read file", str(exc))
            return

        self.session.raw_signal = signal
        self.session.dataset_filename = os.path.basename(path)
        self.file_label.setText(os.path.basename(path))
        self.status_label.setText(f"✓ Loaded {len(signal)} samples. Ready to analyze.")
        self.status_label.setStyleSheet("color: #22C55E;")
        self.next_btn.setEnabled(True)

    def _load_signal(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        elif ext == ".txt":
            try:
                df = pd.read_csv(path, sep=None, engine="python")
            except Exception:
                return np.loadtxt(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        if "voltage" in df.columns:
            return df["voltage"].to_numpy(dtype=float)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric column found in this file.")
        return df[numeric_cols[-1]].to_numpy(dtype=float)

    def continue_to_analysis(self):
        patient_name = self.patient_selector.currentText()
        if not patient_name:
            QMessageBox.warning(self, "No patient selected", "Add a patient first from Patient Management.")
            return
        if self.session.raw_signal is None:
            QMessageBox.warning(self, "No file", "Select a dataset file first.")
            return

        rate_text = self.rate_input.text().strip()
        if not rate_text.isdigit() or int(rate_text) <= 0:
            QMessageBox.warning(self, "Invalid rate", "Sampling rate must be a positive whole number.")
            return

        self.session.patient = self._patients_by_name[patient_name]
        self.session.sampling_rate = int(rate_text)
        self.dataset_ready.emit()
