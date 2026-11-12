import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

import theme
from config import APP_NAME
from database.connection import init_db
from database import users as users_db
from ui.sliding_stack import SlidingStackedWidget
from ui.dashboard import DashboardPage
from ui.patients import PatientsPage
from ui.import_ecg import ImportEcgPage
from ui.analysis import AnalysisPage
from ui.summary import SummaryPage
from ui.report_history import ReportHistoryPage
from ui.settings import SettingsPage
from utils.session import AppSession

NAV_DASHBOARD, NAV_PATIENTS, NAV_IMPORT, NAV_ANALYSIS, NAV_SUMMARY, NAV_HISTORY, NAV_SETTINGS = range(7)


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, doctor_id=None, doctor_name=""):
        super().__init__()
        self.session = AppSession()
        self.session.doctor_id = doctor_id
        self.session.doctor_name = doctor_name

        self.setWindowTitle(f"{APP_NAME}")
        self.resize(1220, 760)
        self.setMinimumSize(1000, 640)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(225)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        heart = QLabel("♥  Cardiac")
        heart.setObjectName("SidebarTitle")
        sub = QLabel("RHYTHM ANALYSIS SYSTEM")
        sub.setObjectName("SidebarSubtitle")
        sidebar_layout.addWidget(heart)
        sidebar_layout.addWidget(sub)

        if doctor_name:
            signed_in = QLabel(f"Signed in as {doctor_name}")
            signed_in.setWordWrap(True)
            signed_in.setStyleSheet(f"color: {theme.TEXT}; padding: 0 20px 14px 20px; font-size: 11px;")
            sidebar_layout.addWidget(signed_in)

        self.nav_buttons = []
        nav_items = [
            ("Dashboard", NAV_DASHBOARD, "dashboard"),
            ("Patients", NAV_PATIENTS, "patients"),
            ("Import ECG Dataset", NAV_IMPORT, "ecg"),
            ("Report History", NAV_HISTORY, "history"),
            ("Settings", NAV_SETTINGS, "profile"),
        ]
        for label, index, icon_name in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("active", index == NAV_DASHBOARD)
            btn.setIcon(QIcon(theme.icon(icon_name)))
            btn.setIconSize(QSize(16, 16))
            btn.clicked.connect(lambda checked=False, i=index: self.go_to_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append((btn, index))

        sidebar_layout.addStretch()
        root_layout.addWidget(sidebar)

        self.stack = SlidingStackedWidget()
        self.dashboard_page = DashboardPage()
        self.patients_page = PatientsPage()
        self.import_page = ImportEcgPage(self.session)
        self.analysis_page = AnalysisPage(self.session)
        self.summary_page = SummaryPage(self.session)
        self.history_page = ReportHistoryPage()
        self.settings_page = SettingsPage(self.session)

        for page in [
            self.dashboard_page, self.patients_page, self.import_page,
            self.analysis_page, self.summary_page, self.history_page, self.settings_page,
        ]:
            self.stack.addWidget(page)

        root_layout.addWidget(self.stack, stretch=1)

        # Wiring
        self.dashboard_page.navigate_requested.connect(self.go_to_page)
        self.patients_page.patients_changed.connect(self.import_page.reload_patient_list)
        self.patients_page.start_ecg_requested.connect(self._on_start_ecg_from_patients)
        self.import_page.dataset_ready.connect(self._on_dataset_ready)
        self.analysis_page.analysis_done.connect(self._on_analysis_done)
        self.analysis_page.back_requested.connect(lambda: self.go_to_page(NAV_IMPORT))
        self.summary_page.back_to_analysis_requested.connect(lambda: self.go_to_page(NAV_ANALYSIS))
        self.summary_page.report_saved.connect(self._on_report_saved)
        self.settings_page.logout_requested.connect(self.logout_requested.emit)
        self.settings_page.profile_updated.connect(self._on_profile_updated)

        self.refresh_all()

    def go_to_page(self, index):
        for btn, idx in self.nav_buttons:
            btn.setProperty("active", idx == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.stack.slide_to_index(index)

        if index == NAV_DASHBOARD:
            self.dashboard_page.refresh()
        elif index == NAV_PATIENTS:
            self.patients_page.refresh()
        elif index == NAV_IMPORT:
            self.import_page.reload_patient_list()
        elif index == NAV_HISTORY:
            self.history_page.refresh()
        elif index == NAV_SETTINGS:
            self.settings_page.refresh()

    def _on_dataset_ready(self):
        self.go_to_page(NAV_ANALYSIS)
        self.analysis_page.run_analysis()

    def _on_start_ecg_from_patients(self, patient_name):
        self.go_to_page(NAV_IMPORT)
        self.import_page.reload_patient_list()
        self.import_page.patient_selector.setCurrentText(patient_name)

    def _on_analysis_done(self):
        self.go_to_page(NAV_SUMMARY)
        self.summary_page.refresh_from_session()

    def _on_report_saved(self):
        self.session.reset_ecg_workflow()
        self.import_page.file_label.setText("No file selected")
        self.import_page.status_label.setText("")
        self.import_page.next_btn.setEnabled(False)
        self.dashboard_page.refresh()
        self.go_to_page(NAV_DASHBOARD)

    def _on_profile_updated(self, new_name):
        # sidebar "Signed in as" label doesn't live-update without a rebuild;
        # acceptable since it's cosmetic and refreshes on next login.
        pass

    def refresh_all(self):
        self.dashboard_page.refresh()
        self.patients_page.refresh()
        self.import_page.reload_patient_list()
        self.history_page.refresh()
        self.settings_page.refresh()


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)
    app.setStyleSheet(theme.STYLESHEET)

    state = {"auth_window": None, "main_window": None}

    def show_auth():
        from auth_window import AuthWindow
        auth = AuthWindow()
        auth.login_successful.connect(show_main)
        state["auth_window"] = auth
        auth.show()

    def show_main(doctor_id, doctor_name):
        state["auth_window"].close()
        state["auth_window"] = None
        window = MainWindow(doctor_id, doctor_name)
        window.logout_requested.connect(handle_logout)
        state["main_window"] = window
        window.show()

    def handle_logout():
        state["main_window"].close()
        state["main_window"] = None
        show_auth()

    show_auth()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
