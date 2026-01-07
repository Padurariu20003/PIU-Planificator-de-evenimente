from PySide6.QtWidgets import (
    QApplication,
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
from core.validators import validate_email

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
            email = validate_email(email)
        except ValueError as ex:
            QMessageBox.warning(
                self,
                "Eroare",
                str(ex),
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
        self.email_edit.setText(email)

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

        self.setStyleSheet("""
        QLabel#TitleLabel {
            font-size: 20px;
            font-weight: bold;
        }
        QLabel#InfoLabel {
            color: #cccccc;
        }
        QLineEdit {
            padding: 10px 16px;
            font-size: 14px;
            border-radius: 6px;
        }
        QPushButton {
            padding: 6px 16px;
            border-radius: 5px;
            border: 1px solid #666666;
        }
        QPushButton:hover {
            border: 2px solid #aaaaaa;
        }
        QPushButton:pressed {
            border: 2px solid #ffffff;
        }
        QPushButton:focus {
            border: 2px solid #ffffff;
        }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)

        main_layout.addStretch()

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        title_label = QLabel("EventEase - Autentificare")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title_label)

        info_label = QLabel(
            "Introduceti emailul si parola pentru autentificare.<br>"
            "Cont implicit administrator: <b>admin@eventease.local</b> / parola: <b>admin</b>"
        )
        info_label.setObjectName("InfoLabel")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        center_layout.addWidget(info_label)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Parola")
        self.password_edit.setEchoMode(QLineEdit.Password)

        for w in (self.email_edit, self.password_edit):
            w.setMinimumWidth(350)
            w.setMaximumWidth(400)

        center_layout.addWidget(self.email_edit, 0, Qt.AlignHCenter)
        center_layout.addWidget(self.password_edit, 0, Qt.AlignHCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.login_button = QPushButton("Autentificare")
        self.register_button = QPushButton("Inregistreaza-te")
        self.guest_button = QPushButton("Intra ca vizitator")
        self.exit_button = QPushButton("Iesire")

        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.register_button)
        buttons_layout.addWidget(self.guest_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.exit_button)

        center_layout.addLayout(buttons_layout)

        main_layout.addWidget(center_widget, 0, Qt.AlignHCenter)

        main_layout.addStretch()

        self.login_button.clicked.connect(self.on_login_clicked)
        self.register_button.clicked.connect(self.on_register_clicked)
        self.guest_button.clicked.connect(self.on_guest_clicked)
        self.exit_button.clicked.connect(self.on_exit_clicked)

    def clear_fields(self):
        self.email_edit.clear()
        self.password_edit.clear()
        self.email_edit.setFocus()

    def on_login_clicked(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        if not email or not password:
            QMessageBox.warning(self, "Eroare", "Introduceti emailul si parola.")
            return
        
        try:
            email = validate_email(email)
        except ValueError as ex:
            QMessageBox.warning(self, "Eroare", str(ex))
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

    def on_exit_clicked(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()