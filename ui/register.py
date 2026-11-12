from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Signal, Qt

import theme
from database import users


class RegisterPage(QWidget):
    registered = Signal(str)
    go_to_login = Signal()

    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        outer = QHBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        container = QWidget()
        container.setFixedWidth(380)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 30, 0, 30)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)
        outer.addWidget(container)

        heart = QLabel("♥")
        heart.setStyleSheet(f"color: {theme.ACCENT}; font-size: 26px;")
        layout.addWidget(heart)

        title = QLabel("Create your account")
        title.setStyleSheet(f"color: {theme.TEXT}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)
        subtitle = QLabel("Clinician sign-up for Cardiac Rhythm Analysis System")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        layout.addWidget(self._label("FULL NAME"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Dr. Ananya Rao")
        layout.addWidget(self.name_input)

        layout.addWidget(self._label("USERNAME"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        layout.addWidget(self.username_input)

        layout.addWidget(self._label("PASSWORD"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("At least 4 characters")
        layout.addWidget(self.password_input)

        layout.addWidget(self._label("CONFIRM PASSWORD"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.returnPressed.connect(self.try_register)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(12)
        register_btn = QPushButton("Create Account")
        register_btn.setObjectName("PrimaryButton")
        register_btn.clicked.connect(self.try_register)
        layout.addWidget(register_btn)

        back_btn = QPushButton("Back to sign in")
        back_btn.clicked.connect(self.go_to_login.emit)
        layout.addWidget(back_btn)

        layout.addStretch()

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("StatLabel")
        return label

    def try_register(self):
        full_name = self.name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing info", "Username and password are required.")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Weak password", "Password must be at least 4 characters.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        try:
            if users.username_exists(username):
                QMessageBox.warning(self, "Already exists", "That username is already taken.")
                return
            users.create_user(username, password, full_name)
        except Exception as exc:
            QMessageBox.critical(self, "Database error", f"Could not reach the database:\n{exc}")
            return

        QMessageBox.information(self, "Account created", "You can now sign in.")
        self.name_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.registered.emit(username)
