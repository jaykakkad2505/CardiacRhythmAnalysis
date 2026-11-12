import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap

import theme
from database import reports as reports_db


class ReportHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_report = None
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 26, 36, 26)
        layout.setSpacing(14)

        title = QLabel("Report History")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Search, filter, and review past ECG reports.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patient or report ID")
        self.search_input.textChanged.connect(self.refresh)
        filter_row.addWidget(self.search_input, stretch=2)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Stable", "Review needed"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        filter_row.addWidget(self.status_filter, stretch=1)
        layout.addLayout(filter_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        table_col = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Report ID", "Patient", "Date & Time", "Heart Rate", "Finding", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        table_col.addWidget(self.table, stretch=1)

        self.pagination_label = QLabel("")
        self.pagination_label.setStyleSheet(f"color: {theme.MUTED}; font-size: 11px;")
        self.pagination_label.setAlignment(Qt.AlignRight)
        table_col.addWidget(self.pagination_label)
        content_row.addLayout(table_col, stretch=2)

        self.preview_card = QFrame()
        self.preview_card.setObjectName("Card")
        self.preview_card.setFixedWidth(280)
        self.preview_layout = QVBoxLayout(self.preview_card)
        self.preview_layout.setContentsMargins(18, 16, 18, 16)
        self.preview_layout.setSpacing(6)
        self.preview_layout.setAlignment(Qt.AlignTop)
        self._render_empty_preview()
        content_row.addWidget(self.preview_card, stretch=1)

        layout.addLayout(content_row, stretch=1)

    def _render_empty_preview(self):
        self._clear_layout(self.preview_layout)
        placeholder = QLabel("Select a report to preview it here.")
        placeholder.setObjectName("PageSubtitle")
        placeholder.setWordWrap(True)
        self.preview_layout.addWidget(placeholder)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def refresh(self):
        term = self.search_input.text().strip()
        status = self.status_filter.currentText()
        status = None if status == "All Statuses" else status

        rows = reports_db.search_reports(term=term or None, status=status)
        self.table.setRowCount(0)
        self._rows_cache = rows

        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["report_code"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["patient_name"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(row["created_at"])))
            hr_text = f"{row['heart_rate']} BPM" if row["heart_rate"] else "-"
            self.table.setItem(r, 3, QTableWidgetItem(hr_text))
            self.table.setItem(r, 4, QTableWidgetItem(row["finding"] or "-"))

            status_item = QTableWidgetItem(row["status"])
            color = theme.GOOD if row["status"] == "Stable" else theme.WARN
            status_item.setForeground(QColor(color))
            self.table.setItem(r, 5, status_item)

        self.pagination_label.setText(f"Showing {len(rows)} of {reports_db.count_reports()} reports")

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row_idx = selected[0].row()
        if row_idx >= len(self._rows_cache):
            return
        report = self._rows_cache[row_idx]
        self.selected_report = report
        self._render_preview(report)

    def _render_preview(self, report):
        self._clear_layout(self.preview_layout)

        header_row = QHBoxLayout()
        header = QLabel(report["report_code"])
        header.setStyleSheet(f"color: {theme.TEXT}; font-size: 15px; font-weight: 700;")
        header_row.addWidget(header)
        header_row.addStretch()
        status_label = QLabel(report["status"])
        color = theme.GOOD if report["status"] == "Stable" else theme.WARN
        status_label.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 11px;")
        header_row.addWidget(status_label)
        self.preview_layout.addLayout(header_row)
        self.preview_layout.addSpacing(6)

        fields = [
            ("Patient", report["patient_name"]),
            ("Date & Time", str(report["created_at"])),
            ("Heart Rate", f"{report['heart_rate']} BPM" if report["heart_rate"] else "-"),
            ("Finding", report["finding"]),
            ("Duration", f"{report['signal_duration']} s" if report["signal_duration"] else "-"),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
            v = QLabel(str(value))
            v.setStyleSheet(f"color: {theme.TEXT}; font-size: 10px;")
            v.setWordWrap(True)
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            self.preview_layout.addLayout(row)

        self.preview_layout.addSpacing(10)
        overview_title = QLabel("ECG OVERVIEW")
        overview_title.setObjectName("StatLabel")
        self.preview_layout.addWidget(overview_title)

        chart_frame = QFrame()
        chart_frame.setFixedHeight(70)
        chart_frame.setStyleSheet(f"background-color: {theme.SURFACE_2}; border-radius: 4px;")
        chart_inner = QVBoxLayout(chart_frame)
        chart_inner.setContentsMargins(4, 4, 4, 4)
        chart_path = report.get("waveform_chart_path")
        if chart_path and os.path.exists(chart_path):
            img_label = QLabel()
            pixmap = QPixmap(chart_path)
            img_label.setPixmap(pixmap.scaledToWidth(230, Qt.SmoothTransformation))
            chart_inner.addWidget(img_label)
        else:
            no_chart = QLabel("No chart available")
            no_chart.setStyleSheet(f"color: {theme.MUTED}; font-size: 10px;")
            no_chart.setAlignment(Qt.AlignCenter)
            chart_inner.addWidget(no_chart)
        self.preview_layout.addWidget(chart_frame)

        self.preview_layout.addSpacing(10)
        mark_stable_btn = QPushButton("Mark as Stable")
        mark_stable_btn.clicked.connect(lambda: self._update_status(report, "Stable"))
        self.preview_layout.addWidget(mark_stable_btn)

        mark_review_btn = QPushButton("Mark as Review Needed")
        mark_review_btn.clicked.connect(lambda: self._update_status(report, "Review needed"))
        self.preview_layout.addWidget(mark_review_btn)

        delete_btn = QPushButton("Delete Report")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(lambda: self._delete_report(report))
        self.preview_layout.addWidget(delete_btn)

    def _update_status(self, report, new_status):
        reports_db.update_report_status(report["id"], new_status, note="Status updated from Report History")
        self.refresh()

    def _delete_report(self, report):
        reply = QMessageBox.question(self, "Delete Report", f"Delete report {report['report_code']}?")
        if reply == QMessageBox.Yes:
            reports_db.delete_report(report["id"])
            self._render_empty_preview()
            self.refresh()
