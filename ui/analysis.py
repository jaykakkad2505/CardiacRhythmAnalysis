import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import theme
from utils.ecg_processing import process_ecg, ECGValidationError

PARAM_ICONS = {
    "heart_rate": ("♥", "#EF4444"),
    "rr_interval": ("↝", "#8B5CF6"),
    "pr_interval": ("◷", "#3B82F6"),
    "qrs_duration": ("⌁", "#22C55E"),
    "qt_interval": ("⌇", "#EAB308"),
    "qtc_interval": ("⌇", "#F97316"),
    "beat_count": ("⛶", "#14B8A6"),
    "signal_duration": ("⏱", "#EAB308"),
}
PARAM_LABELS = {
    "heart_rate": ("Heart Rate", "BPM"), "rr_interval": ("RR Interval", "s"),
    "pr_interval": ("PR Interval", "s"), "qrs_duration": ("QRS Duration", "s"),
    "qt_interval": ("QT Interval", "s"), "qtc_interval": ("QTc Interval", "s"),
    "beat_count": ("Beat Count", ""), "signal_duration": ("Duration", "s"),
}


class AnalysisPage(QWidget):
    analysis_done = Signal()
    back_requested = Signal()

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(12)

        title = QLabel("ECG Analysis")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Visualize, process, and interpret the selected signal.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # --- Patient / dataset info bar ---
        info_bar = QFrame()
        info_bar.setObjectName("Card")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(16, 10, 16, 10)

        patient_box = QVBoxLayout()
        patient_caption = QLabel("SELECTED PATIENT")
        patient_caption.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
        patient_box.addWidget(patient_caption)
        self.patient_value = QLabel("--")
        self.patient_value.setStyleSheet(f"color: {theme.TEXT}; font-size: 13px; font-weight: 600;")
        patient_box.addWidget(self.patient_value)
        info_layout.addLayout(patient_box)
        info_layout.addSpacing(30)

        dataset_box = QVBoxLayout()
        dataset_caption = QLabel("DATASET")
        dataset_caption.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
        dataset_box.addWidget(dataset_caption)
        self.dataset_value = QLabel("--")
        self.dataset_value.setStyleSheet(f"color: {theme.TEXT}; font-size: 13px; font-weight: 600;")
        dataset_box.addWidget(self.dataset_value)
        info_layout.addLayout(dataset_box)
        info_layout.addStretch()
        layout.addWidget(info_bar)

        main_row = QHBoxLayout()
        main_row.setSpacing(16)

        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        self.figure = Figure(figsize=(6, 3.0), facecolor=theme.SURFACE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        chart_layout.addWidget(self.canvas)
        main_row.addWidget(chart_card, stretch=3)

        side_card = QFrame()
        side_card.setObjectName("Card")
        side_layout = QVBoxLayout(side_card)
        side_layout.setContentsMargins(18, 16, 18, 16)
        side_layout.setSpacing(6)
        pipeline_title = QLabel("ANALYSIS PIPELINE")
        pipeline_title.setObjectName("StatLabel")
        side_layout.addWidget(pipeline_title)

        self.step_rows = []
        for i, step in enumerate(["Dataset validated", "Signal cleaned", "R-peak detection", "Wave delineation"], start=1):
            row = QHBoxLayout()
            circle = QLabel(str(i))
            circle.setFixedSize(18, 18)
            circle.setAlignment(Qt.AlignCenter)
            circle.setStyleSheet(f"background-color: {theme.SURFACE_2}; color: {theme.MUTED}; border-radius: 9px; font-size: 10px;")
            row.addWidget(circle)
            name = QLabel(step)
            name.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
            row.addWidget(name)
            row.addStretch()
            status = QLabel("Pending")
            status.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
            row.addWidget(status)
            side_layout.addLayout(row)
            self.step_rows.append((circle, name, status))

        side_layout.addSpacing(12)
        params_title = QLabel("SIGNAL PARAMETERS")
        params_title.setObjectName("StatLabel")
        side_layout.addWidget(params_title)

        params_grid = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        self.param_cards = {}
        for i, key in enumerate(PARAM_LABELS):
            card = self._make_param_card(key)
            (col1 if i % 2 == 0 else col2).addWidget(card)
        params_grid.addLayout(col1)
        params_grid.addLayout(col2)
        side_layout.addLayout(params_grid)

        side_layout.addStretch()
        main_row.addWidget(side_card, stretch=2)
        layout.addLayout(main_row, stretch=1)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.back_requested.emit)
        btn_row.addWidget(back_btn)
        btn_row.addStretch()
        self.summary_btn = QPushButton("View ECG Summary  →")
        self.summary_btn.setObjectName("PrimaryButton")
        self.summary_btn.setEnabled(False)
        self.summary_btn.clicked.connect(self.analysis_done.emit)
        btn_row.addWidget(self.summary_btn)
        layout.addLayout(btn_row)

    def _make_param_card(self, key):
        label, unit = PARAM_LABELS[key]
        icon_char, color = PARAM_ICONS[key]
        card = QFrame()
        card.setStyleSheet(f"background-color: {theme.SURFACE_2}; border-radius: 4px;")
        h = QHBoxLayout(card)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(6)

        icon = QLabel(icon_char)
        icon.setFixedSize(20, 20)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"color: {color}; font-size: 12px;")
        h.addWidget(icon)

        v = QVBoxLayout()
        v.setSpacing(0)
        name_label = QLabel(label)
        name_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")
        v.addWidget(name_label)
        value_label = QLabel("--")
        value_label.setStyleSheet(f"color: {theme.TEXT}; font-size: 13px; font-weight: 700;")
        v.addWidget(value_label)
        h.addLayout(v)

        self.param_cards[key] = value_label
        return card

    def run_analysis(self):
        """Called when this page becomes active with a freshly loaded signal."""
        self.summary_btn.setEnabled(False)

        patient = self.session.patient
        self.patient_value.setText(patient["name"] if patient else "--")
        self.dataset_value.setText(self.session.dataset_filename or "--")

        for circle, name, status in self.step_rows:
            circle.setStyleSheet(f"background-color: {theme.SURFACE_2}; color: {theme.MUTED}; border-radius: 9px; font-size: 10px;")
            status.setText("Pending")
            status.setStyleSheet(f"color: {theme.MUTED}; font-size: 9px;")

        if self.session.raw_signal is None:
            self._draw_empty("No dataset loaded.")
            return

        try:
            result = process_ecg(self.session.raw_signal, self.session.sampling_rate)
        except ECGValidationError as exc:
            QMessageBox.warning(self, "Analysis failed", str(exc))
            self._draw_empty(str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Unexpected error", str(exc))
            self._draw_empty("Unexpected error during analysis.")
            return

        self.session.result = result

        for circle, name, status in self.step_rows:
            circle.setStyleSheet(f"background-color: {theme.GOOD}; color: white; border-radius: 9px; font-size: 10px;")
            status.setText("Complete")
            status.setStyleSheet(f"color: {theme.GOOD}; font-size: 9px;")

        for key, value_label in self.param_cards.items():
            v = result["params"].get(key)
            _, unit = PARAM_LABELS[key]
            if v is None:
                value_label.setText("--")
            else:
                value_label.setText(f"{v} {unit}".strip())

        self._draw_waveform(result)
        self.summary_btn.setEnabled(True)

    def _style_axes(self, ax):
        ax.set_facecolor(theme.SURFACE)
        ax.tick_params(colors=theme.MUTED, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(theme.BORDER)

    def _draw_empty(self, message):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._style_axes(ax)
        ax.text(0.5, 0.5, message, ha="center", va="center", color=theme.MUTED, transform=ax.transAxes, wrap=True)
        self.canvas.draw()

    def _draw_waveform(self, result):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._style_axes(ax)

        signal = result["cleaned_signal"]
        sr = self.session.sampling_rate
        t = np.arange(len(signal)) / sr
        ax.plot(t, signal, color=theme.TEXT, linewidth=0.8)

        rpeaks = result["rpeaks"]
        if len(rpeaks):
            peak_t = np.array(rpeaks) / sr
            peak_y = np.array(signal)[np.array(rpeaks)]
            ax.scatter(peak_t, peak_y, color=theme.ACCENT, s=24, zorder=3, label="R-peak")
            ax.legend(loc="upper right", fontsize=7, facecolor=theme.SURFACE, edgecolor=theme.BORDER, labelcolor=theme.TEXT)

        ax.set_xlabel("Time (s)", color=theme.MUTED, fontsize=8)
        self.figure.tight_layout()
        self.canvas.draw()
