from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from services.auth_service import login as auth_login


class LoginView(QWidget):
    login_as_admin = Signal()
    login_as_user = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("EventEase")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Introduceti emailul si parola pentru autentificare.\n"
            "Utilizator implicit: admin@eventease.local / parola: admin"
        )
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setText("admin@eventease.local")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Parola")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText("admin")

        main_layout.addWidget(self.email_edit)
        main_layout.addWidget(self.password_edit)

        main_layout.addStretch()

        button_layout = QHBoxLayout()

        self.login_button = QPushButton("Autentificare")
        self.guest_button = QPushButton("Intra ca vizitator")

        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.guest_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        main_layout.addStretch()

        self.login_button.clicked.connect(self.on_login_clicked)
        self.guest_button.clicked.connect(self.on_guest_clicked)

    def on_login_clicked(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        if not email or not password:
            QMessageBox.warning(self, "Eroare", "Introduceti emailul si parola.")
            return

        role = auth_login(email, password)

        if role is None:
            QMessageBox.critical(
                self,
                "Autentificare esuata",
                "Email sau parola incorecte.",
            )
            return

        if role == "admin":
            self.login_as_admin.emit()
        else:
            self.login_as_user.emit()

    def on_guest_clicked(self) -> None:
        self.login_as_user.emit()
