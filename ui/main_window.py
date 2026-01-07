from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QToolBar, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from .login_view import LoginView
from .admin.view import AdminEventsView 
from .user.view import UserEventsView
from core import session
from .themes import LIGHT_THEME, DARK_THEME

class MainWindow(QMainWindow):
    PAGE_LOGIN = 0
    PAGE_ADMIN = 1
    PAGE_USER = 2

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("EventEase - Planificator de evenimente")
        self.resize(900, 600)
        self.is_dark_mode = False
        self.apply_theme() 
        
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False) 
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.toggle_theme_action = QAction("🌙 Dark Mode", self)
        self.toggle_theme_action.triggered.connect(self.on_toggle_theme)
        toolbar.addAction(self.toggle_theme_action)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.login_view = LoginView()
        self.admin_view = AdminEventsView()
        self.user_view = UserEventsView()

        self.stack.addWidget(self.login_view)
        self.stack.addWidget(self.admin_view)
        self.stack.addWidget(self.user_view)

        self.login_view.login_as_admin.connect(self.on_login_admin)
        self.login_view.login_as_user.connect(self.on_login_user)

        self.admin_view.back_to_login.connect(self.on_logout)
        self.user_view.back_to_login.connect(self.on_logout)

        self.status = self.statusBar()
        self.update_status_bar()
        self.stack.setCurrentIndex(self.PAGE_LOGIN)

    def on_toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.toggle_theme_action.setText("☀️ Light Mode")
        else:
            self.toggle_theme_action.setText("🌙 Dark Mode")
        self.apply_theme() 

    def apply_theme(self):
        app = QApplication.instance()
        if app:
            if self.is_dark_mode:
                app.setStyleSheet(DARK_THEME)
            else:
                app.setStyleSheet(LIGHT_THEME)

    def update_status_bar(self) -> None:
        email, role = session.get_current_user()
        if not email and not role:
            self.status.showMessage("Neautentificat", 0)
        elif role == "admin":
            self.status.showMessage(f"Autentificat ca administrator: {email}", 0)
        else:
            self.status.showMessage(f"Autentificat ca utilizator: {email}" if email else "Utilizator vizitator", 0)

    def on_login_admin(self) -> None:
        self.stack.setCurrentIndex(self.PAGE_ADMIN)
        self.update_status_bar()

    def on_login_user(self) -> None:
        self.stack.setCurrentIndex(self.PAGE_USER)
        self.update_status_bar()

    def on_logout(self) -> None:
        reply = QMessageBox.question(
            self, "Confirmare", 
            "Sigur doriti sa va deconectati?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes: return

        session.clear_current_user()
        
        self.login_view.clear_fields() 
        
        self.stack.setCurrentIndex(self.PAGE_LOGIN)
        self.update_status_bar()