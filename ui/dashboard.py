from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import theme
from database import patients, reports


def make_card():
    card = QFrame()
    card.setObjectName("Card")
    return card


class DashboardPage(QWidget):
    navigate_requested = Signal(int)

    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 26, 36, 26)
        layout.setSpacing(16)

        # --- Top bar: title + search + bell + avatar + date ---
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Quick stats and shortcuts into patient records, ECG import, and report history.")
        subtitle.setObjectName("PageSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        search_box = QLineEdit()
        search_box.setPlaceholderText("Search patients, reports...")
        search_box.setFixedWidth(220)
        header.addWidget(search_box)

        bell = QLabel("🔔")
        bell.setStyleSheet(f"font-size: 16px; padding: 0 8px; color: {theme.TEXT};")
        header.addWidget(bell)

        avatar = QLabel("👤")
        avatar.setStyleSheet(
            f"font-size: 14px; background-color: {theme.SURFACE_2}; border-radius: 14px; "
            f"padding: 6px; color: {theme.TEXT};"
        )
        header.addWidget(avatar)

        date_label = QLabel(datetime.now().strftime("%d %b %Y"))
        date_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px; padding-left: 6px;")
        header.addWidget(date_label)
        layout.addLayout(header)

        self.review_banner = QLabel()
        self.review_banner.setObjectName("AlertBanner")
        self.review_banner.setWordWrap(True)
        self.review_banner.hide()
        layout.addWidget(self.review_banner)

        # --- Stat cards with icon badges ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self.total_patients_card, self.total_patients_value = self._stat_card("Total Patients", "patients")
        self.total_reports_card, self.total_reports_value = self._stat_card("Total ECG Analyses", "ecg")
        self.review_card, self.review_value = self._stat_card("Recent Alerts", "calendar")
        self.latest_hr_card, self.latest_hr_value = self._stat_card("Reports Available", "records")
        stats_row.addWidget(self.total_patients_card)
        stats_row.addWidget(self.total_reports_card)
        stats_row.addWidget(self.review_card)
        stats_row.addWidget(self.latest_hr_card)
        layout.addLayout(stats_row)

        # --- Quick Actions ---
        actions_card = make_card()
        actions_layout = QHBoxLayout(actions_card)
        actions_layout.setContentsMargins(16, 14, 16, 14)
        actions_layout.setSpacing(10)
        quick_actions = [
            ("Add Patient", "patients", 1),
            ("Import ECG Dataset", "ecg", 2),
            ("Report History", "history", 5),
            ("Settings", "profile", 6),
        ]
        for label, icon_name, target_index in quick_actions:
            btn = QPushButton(f"  {label}")
            btn.setIcon(QIcon(theme.icon(icon_name)))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=target_index: self.navigate_requested.emit(i))
            actions_layout.addWidget(btn)
        layout.addWidget(actions_card)

        # --- ECG overview chart + Recent Reports ---
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        chart_card = make_card()
        chart_card.setFixedHeight(230)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 14, 16, 14)
        chart_title = QLabel("ECG SIGNAL OVERVIEW")
        chart_title.setObjectName("StatLabel")
        chart_layout.addWidget(chart_title)
        self.figure = Figure(figsize=(4, 2), facecolor=theme.SURFACE)
        self.canvas = FigureCanvasQTAgg(self.figure)
        chart_layout.addWidget(self.canvas, stretch=1)
        mid_row.addWidget(chart_card, stretch=3)

        recent_reports_card = make_card()
        recent_reports_card.setFixedHeight(230)
        rr_layout = QVBoxLayout(recent_reports_card)
        rr_layout.setContentsMargins(18, 14, 18, 14)
        rr_layout.setSpacing(8)
        rr_layout.setAlignment(Qt.AlignTop)
        rr_title = QLabel("RECENT REPORTS")
        rr_title.setObjectName("StatLabel")
        rr_layout.addWidget(rr_title)
        self.recent_reports_layout = QVBoxLayout()
        self.recent_reports_layout.setSpacing(6)
        rr_layout.addLayout(self.recent_reports_layout)
        rr_layout.addStretch()
        mid_row.addWidget(recent_reports_card, stretch=2)

        layout.addLayout(mid_row)

        # --- Recent Patients table ---
        patients_card = make_card()
        patients_layout = QVBoxLayout(patients_card)
        patients_layout.setContentsMargins(18, 14, 18, 14)
        patients_layout.setSpacing(8)
        pc_title = QLabel("RECENT PATIENTS")
        pc_title.setObjectName("StatLabel")
        patients_layout.addWidget(pc_title)

        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(4)
        self.patients_table.setHorizontalHeaderLabels(["Patient ID", "Name", "Age", "Gender"])
        self.patients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.patients_table.verticalHeader().setVisible(False)
        self.patients_table.verticalHeader().setDefaultSectionSize(34)
        self.patients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.patients_table.setAlternatingRowColors(True)
        self.patients_table.setFixedHeight(180)
        patients_layout.addWidget(self.patients_table)

        layout.addWidget(patients_card)

    def _stat_card(self, label_text, icon_name):
        card = make_card()
        h = QHBoxLayout(card)
        h.setContentsMargins(18, 16, 18, 16)
        h.setSpacing(12)

        badge = QLabel()
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"background-color: {theme.ACCENT_2}; border-radius: 19px;")
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(theme.icon(icon_name)).pixmap(18, 18))
        icon_label.setAlignment(Qt.AlignCenter)
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.addWidget(icon_label)
        h.addWidget(badge)

        v = QVBoxLayout()
        value = QLabel("--")
        value.setObjectName("StatValue")
        value.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {theme.TEXT};")
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        v.addWidget(value)
        v.addWidget(label)
        h.addLayout(v)
        h.addStretch()
        return card, value

    def refresh(self):
        all_reports = reports.get_all_reports()
        all_patients = patients.get_all_patients()
        review_count = reports.count_reports_needing_review()

        self.total_patients_value.setText(str(len(all_patients)))
        self.total_reports_value.setText(str(len(all_reports)))
        self.review_value.setText(str(review_count))
        self.latest_hr_value.setText(str(len(all_reports)))

        if review_count > 0:
            self.review_banner.setText(f"⚠ {review_count} report(s) currently flagged as \"Review needed\".")
            self.review_banner.show()
        else:
            self.review_banner.hide()

        self._populate_recent_reports(all_reports[:5])
        self._populate_recent_patients(all_patients[:6])
        self._render_chart(all_reports[:10])

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_recent_reports(self, rows):
        self._clear_layout(self.recent_reports_layout)
        if not rows:
            empty = QLabel("No reports yet.")
            empty.setObjectName("PageSubtitle")
            self.recent_reports_layout.addWidget(empty)
            return
        for row in rows:
            color = theme.GOOD if row["status"] == "Stable" else theme.WARN
            entry = QLabel(
                f"<b>{row['report_code']}</b> · {row['patient_name']}<br>"
                f"<span style='color:{color}; font-size:10px;'>{row['status']}</span>"
            )
            entry.setStyleSheet(f"color: {theme.TEXT}; font-size: 11px;")
            self.recent_reports_layout.addWidget(entry)

    def _populate_recent_patients(self, rows):
        self.patients_table.setRowCount(0)
        for row in rows:
            r = self.patients_table.rowCount()
            self.patients_table.insertRow(r)
            self.patients_table.setItem(r, 0, QTableWidgetItem(row["patient_code"]))
            self.patients_table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.patients_table.setItem(r, 2, QTableWidgetItem(str(row["age"]) if row["age"] else ""))
            self.patients_table.setItem(r, 3, QTableWidgetItem(row["gender"] or ""))

    def _style_axes(self, ax):
        ax.set_facecolor(theme.SURFACE)
        ax.tick_params(colors=theme.MUTED, labelsize=6.5)
        for spine in ax.spines.values():
            spine.set_color(theme.BORDER)

    def _render_chart(self, recent_reports_desc):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        self._style_axes(ax)

        rows_asc = list(reversed(recent_reports_desc))
        if len(rows_asc) < 2:
            ax.text(0.5, 0.5, "Import ECG data to see trends", ha="center", va="center",
                     color=theme.MUTED, transform=ax.transAxes, fontsize=8)
            self.canvas.draw()
            return

        hrs = [r["heart_rate"] or 0 for r in rows_asc]
        colors = [theme.GOOD if r["status"] == "Stable" else theme.WARN for r in rows_asc]
        x = range(len(hrs))
        ax.plot(x, hrs, color=theme.ACCENT, linewidth=1.2)
        ax.scatter(x, hrs, c=colors, s=22, zorder=3)
        ax.set_xticks([])
        ax.set_ylabel("BPM", color=theme.MUTED, fontsize=7.5)
        self.figure.tight_layout()
        self.canvas.draw()
