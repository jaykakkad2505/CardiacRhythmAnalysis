import os
from datetime import datetime

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import theme
from database import reports as reports_db
from reports.report_generator import generate_ecg_report_pdf
from config import REPORT_CHARTS_DIR

CORE_PARAMS = [
    ("heart_rate", "Heart Rate", "BPM", "♥", "#EF4444"),
    ("rr_interval", "RR Interval", "s", "◷", "#3B82F6"),
    ("beat_count", "Beat Count", "", "⛶", "#14B8A6"),
    ("signal_duration", "Signal Duration", "s", "⏱", "#EAB308"),
]


class SummaryPage(QWidget):
    back_to_analysis_requested = Signal()
    report_saved = Signal()

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 22, 36, 22)
        layout.setSpacing(12)

        title = QLabel("ECG Summary")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Review calculated parameters and the automated finding before generating the clinical report.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        info_bar = QFrame()
        info_bar.setObjectName("Card")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(16, 10, 16, 10)
        for attr, caption in [("patient_value", "PATIENT"), ("patient_id_value", "PATIENT ID"), ("dataset_value", "DATASET")]:
            box = QVBoxLayout()
            cap = QLabel(caption)
            cap.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
            box.addWidget(cap)
            val = QLabel("--")
            val.setStyleSheet(f"color: {theme.TEXT}; font-size: 12px; font-weight: 600;")
            box.addWidget(val)
            setattr(self, attr, val)
            info_layout.addLayout(box)
            info_layout.addSpacing(24)
        info_layout.addStretch()
        layout.addWidget(info_bar)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_card.setFixedHeight(190)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(14, 10, 14, 10)
        chart_title = QLabel("ECG WAVEFORM WITH DETECTED R PEAKS")
        chart_title.setObjectName("StatLabel")
        chart_layout.addWidget(chart_title)
        self.figure = Figure(figsize=(5, 1.6), facecolor=theme.SURFACE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        chart_layout.addWidget(self.canvas, stretch=1)
        top_row.addWidget(chart_card, stretch=3)

        finding_card = QFrame()
        finding_card.setObjectName("Card")
        finding_card.setFixedHeight(190)
        finding_layout = QVBoxLayout(finding_card)
        finding_layout.setContentsMargins(18, 14, 18, 14)
        finding_layout.setSpacing(6)
        finding_layout.setAlignment(Qt.AlignTop)
        finding_title = QLabel("AUTOMATED FINDING")
        finding_title.setObjectName("StatLabel")
        finding_layout.addWidget(finding_title)
        self.finding_label = QLabel("--")
        self.finding_label.setWordWrap(True)
        self.finding_label.setStyleSheet("font-size: 17px; font-weight: 700;")
        finding_layout.addWidget(self.finding_label)
        self.flags_label = QLabel("")
        self.flags_label.setWordWrap(True)
        self.flags_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
        finding_layout.addWidget(self.flags_label)
        finding_layout.addStretch()
        disclaimer = QLabel("For clinical review only.")
        disclaimer.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px; font-style: italic;")
        finding_layout.addWidget(disclaimer)
        top_row.addWidget(finding_card, stretch=2)
        layout.addLayout(top_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.param_values = {}
        for key, label, unit, icon_char, color in CORE_PARAMS:
            card = QFrame()
            card.setObjectName("Card")
            h = QHBoxLayout(card)
            h.setContentsMargins(12, 10, 12, 10)
            icon = QLabel(icon_char)
            icon.setFixedSize(26, 26)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet(f"color: {color}; font-size: 14px; background-color: {theme.SURFACE_2}; border-radius: 13px;")
            h.addWidget(icon)
            v = QVBoxLayout()
            v.setSpacing(0)
            name_lbl = QLabel(label.upper())
            name_lbl.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
            v.addWidget(name_lbl)
            value_lbl = QLabel("--")
            value_lbl.setStyleSheet(f"color: {theme.TEXT}; font-size: 15px; font-weight: 700;")
            v.addWidget(value_lbl)
            h.addLayout(v)
            self.param_values[key] = (value_lbl, unit)
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        timeline_card = QFrame()
        timeline_card.setObjectName("Card")
        timeline_layout = QVBoxLayout(timeline_card)
        timeline_layout.setContentsMargins(16, 12, 16, 12)
        timeline_layout.setSpacing(6)
        timeline_title = QLabel("PROCESSING TIMELINE")
        timeline_title.setObjectName("StatLabel")
        timeline_layout.addWidget(timeline_title)

        steps_row = QHBoxLayout()
        self.timeline_labels = []
        for step in ["Dataset validated", "Filtered", "Peaks detected", "Parameters calculated"]:
            box = QVBoxLayout()
            box.setAlignment(Qt.AlignCenter)
            check = QLabel("✓")
            check.setFixedSize(20, 20)
            check.setAlignment(Qt.AlignCenter)
            check.setStyleSheet(f"background-color: {theme.GOOD}; color: white; border-radius: 10px; font-size: 11px;")
            box.addWidget(check, alignment=Qt.AlignHCenter)
            name = QLabel(step)
            name.setStyleSheet(f"color: {theme.TEXT}; font-size: 10px;")
            name.setAlignment(Qt.AlignCenter)
            box.addWidget(name)
            ts = QLabel("--")
            ts.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
            ts.setAlignment(Qt.AlignCenter)
            box.addWidget(ts)
            steps_row.addLayout(box)
            self.timeline_labels.append(ts)
        timeline_layout.addLayout(steps_row)
        layout.addWidget(timeline_card)

        notes_card = QFrame()
        notes_card.setObjectName("Card")
        notes_layout = QVBoxLayout(notes_card)
        notes_layout.setContentsMargins(16, 10, 16, 10)
        notes_title = QLabel("CLINICIAN NOTES (OPTIONAL)")
        notes_title.setObjectName("StatLabel")
        notes_layout.addWidget(notes_title)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any clinical notes or observations here...")
        self.notes_input.setFixedHeight(50)
        notes_layout.addWidget(self.notes_input)
        layout.addWidget(notes_card)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("← Back to Analysis")
        back_btn.clicked.connect(self.back_to_analysis_requested.emit)
        btn_row.addWidget(back_btn)
        btn_row.addStretch()
        self.save_btn = QPushButton("Generate PDF Report")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(self.save_and_generate)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def refresh_from_session(self):
        result = self.session.result
        patient = self.session.patient
        if not result or not patient:
            return

        self.patient_value.setText(patient["name"])
        self.patient_id_value.setText(patient["patient_code"])
        self.dataset_value.setText(self.session.dataset_filename or "-")

        for key, (value_label, unit) in self.param_values.items():
            v = result["params"].get(key)
            value_label.setText("--" if v is None else f"{v} {unit}".strip())

        is_stable = result["status"] == "Stable"
        color = theme.GOOD if is_stable else theme.WARN
        self.finding_label.setText(("✓ " if is_stable else "⚠ ") + result["finding"])
        self.finding_label.setStyleSheet(f"color: {color}; font-size: 17px; font-weight: 700;")
        self.flags_label.setText(", ".join(result["flags"]) if result["flags"] else "All parameters within normal range.")
        self.notes_input.clear()

        now_str = datetime.now().strftime("%H:%M:%S")
        for ts in self.timeline_labels:
            ts.setText(f"Completed {now_str}")

        self._draw_mini_waveform(result)

    def _draw_mini_waveform(self, result):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(theme.SURFACE)
        ax.tick_params(colors=theme.MUTED, labelsize=6)
        for spine in ax.spines.values():
            spine.set_color(theme.BORDER)

        signal = result["cleaned_signal"]
        sr = self.session.sampling_rate
        t = np.arange(len(signal)) / sr
        ax.plot(t, signal, color=theme.TEXT, linewidth=0.7)

        rpeaks = result["rpeaks"]
        if len(rpeaks):
            peak_t = np.array(rpeaks) / sr
            peak_y = np.array(signal)[np.array(rpeaks)]
            ax.scatter(peak_t, peak_y, color=theme.ACCENT, s=16, zorder=3)

        ax.set_xlabel("Time (s)", color=theme.MUTED, fontsize=7)
        self.figure.tight_layout()
        self.canvas.draw()

    def save_and_generate(self):
        result = self.session.result
        patient = self.session.patient
        if not result or not patient:
            QMessageBox.warning(self, "Nothing to save", "Run an analysis first.")
            return

        default_name = f"{patient['name'].replace(' ', '_')}_ECG_Report.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_name, "PDF Files (*.pdf)")
        if not path:
            return

        clinician_notes = self.notes_input.toPlainText().strip()

        try:
            os.makedirs(REPORT_CHARTS_DIR, exist_ok=True)
            chart_path = self._save_report_chart_image(patient, result)

            report_code, report_id = reports_db.create_report(
                patient_id=patient["id"],
                dataset_filename=self.session.dataset_filename,
                params=result["params"],
                finding=result["finding"],
                status=result["status"],
                clinician_notes=clinician_notes,
                waveform_chart_path=chart_path,
                created_by=self.session.doctor_id,
            )
            report_row = reports_db.get_report_by_id(report_id)

            generate_ecg_report_pdf(
                report_row=report_row,
                patient_row=patient,
                doctor_name=self.session.doctor_name,
                cleaned_signal=result["cleaned_signal"],
                sampling_rate=self.session.sampling_rate,
                rpeaks=result["rpeaks"],
                output_path=path,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Could not save report", str(exc))
            return

        QMessageBox.information(self, "Saved", f"Report {report_code} saved and PDF generated:\n{path}")
        self.report_saved.emit()

    def _save_report_chart_image(self, patient, result):
        """Saves a small waveform chart PNG for Report History's preview
        panel, matching the mockup's 'ECG Overview' mini chart."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        signal = result["cleaned_signal"]
        sr = self.session.sampling_rate
        t = np.arange(len(signal)) / sr

        fig, ax = plt.subplots(figsize=(3, 1), dpi=150)
        fig.patch.set_facecolor(theme.SURFACE)
        ax.set_facecolor(theme.SURFACE)
        ax.plot(t, signal, color=theme.GOOD, linewidth=0.8)
        ax.axis("off")
        fig.tight_layout(pad=0.2)

        safe_name = "".join(c if c.isalnum() else "_" for c in patient["name"])
        safe_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{safe_time}.png"
        path = os.path.join(REPORT_CHARTS_DIR, filename)
        fig.savefig(path, facecolor=theme.SURFACE)
        plt.close(fig)
        return path
