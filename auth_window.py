from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Signal

from ui.login import LoginPage
from ui.register import RegisterPage


class AuthWindow(QMainWindow):
    login_successful = Signal(int, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cardiac Rhythm Analysis System — Sign In")
        self.resize(820, 560)
        self.setMinimumSize(700, 520)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()
        self.register_page = RegisterPage()
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)

        self.login_page.login_ok.connect(self.login_successful.emit)
        self.login_page.go_to_register.connect(lambda: self.stack.setCurrentIndex(1))
        self.register_page.go_to_login.connect(lambda: self.stack.setCurrentIndex(0))
        self.register_page.registered.connect(self._prefill_login)

    def _prefill_login(self, username):
        self.login_page.username_input.setText(username)
        self.stack.setCurrentIndex(0)
