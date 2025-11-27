from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal

from services.auth_service import login as auth_login, create_user
from core import session


class RegisterDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Inregistrare utilizator")

        layout = QFormLayout(self)

        self.email_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_confirm_edit = QLineEdit()

        self.email_edit.setPlaceholderText("Email")
        self.password_edit.setPlaceholderText("Parola")
        self.password_confirm_edit.setPlaceholderText("Confirmare parola")

        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_confirm_edit.setEchoMode(QLineEdit.Password)

        layout.addRow("Email:", self.email_edit)
        layout.addRow("Parola:", self.password_edit)
        layout.addRow("Confirmare parola:", self.password_confirm_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def on_accept(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        password_confirm = self.password_confirm_edit.text()

        if not email or not password or not password_confirm:
            QMessageBox.warning(
                self,
                "Eroare",
                "Completati toate campurile.",
            )
            return

        if password != password_confirm:
            QMessageBox.warning(
                self,
                "Eroare",
                "Parola si confirmarea nu coincid.",
            )
            return

        try:
            create_user(email, password)
        except ValueError as ex:
            QMessageBox.critical(
                self,
                "Inregistrare esuata",
                str(ex),
            )
            return

        QMessageBox.information(
            self,
            "Succes",
            "Contul a fost creat cu succes. Va puteti autentifica acum.",
        )
        self.accept()

    def get_email(self) -> str:
        return self.email_edit.text().strip()


class LoginView(QWidget):
    login_as_admin = Signal()
    login_as_user = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("EventEase - Autentificare")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Introduceti emailul si parola pentru autentificare.\n"
            "Cont implicit administrator: admin@eventease.local / parola: admin"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
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

        buttons_layout = QHBoxLayout()

        self.login_button = QPushButton("Autentificare")
        self.register_button = QPushButton("Inregistreaza-te")
        self.guest_button = QPushButton("Intra ca vizitator")

        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.register_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.guest_button)

        main_layout.addLayout(buttons_layout)

        main_layout.addStretch()

        self.login_button.clicked.connect(self.on_login_clicked)
        self.register_button.clicked.connect(self.on_register_clicked)
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

        session.set_current_user(email, role)

        if role == "admin":
            self.login_as_admin.emit()
        else:
            self.login_as_user.emit()

    def on_register_clicked(self) -> None:
        dialog = RegisterDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            email = dialog.get_email()
            if email:
                self.email_edit.setText(email)
                self.password_edit.clear()

    def on_guest_clicked(self) -> None:
        session.set_current_user("", "user")
        self.login_as_user.emit()
