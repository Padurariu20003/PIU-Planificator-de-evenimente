from PySide6.QtWidgets import QMainWindow, QStackedWidget
from .login_view import LoginView
from .admin_events_view import AdminEventsView
from .user_events_view import UserEventsView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("EventEase")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_view = LoginView()
        self.stack.addWidget(self.login_view)

        self.admin_view = AdminEventsView()
        self.stack.addWidget(self.admin_view)

        self.user_view = UserEventsView()
        self.stack.addWidget(self.user_view)

        self.stack.setCurrentWidget(self.login_view)

        self.login_view.login_as_admin.connect(self.show_admin_view)
        self.login_view.login_as_user.connect(self.show_user_view)

        self.admin_view.back_to_login.connect(self.show_login_view)
        self.user_view.back_to_login.connect(self.show_login_view)


    def show_login_view(self) -> None:
        self.stack.setCurrentWidget(self.login_view)

    def show_admin_view(self) -> None:
        self.stack.setCurrentWidget(self.admin_view)

    def show_user_view(self) -> None:
        self.stack.setCurrentWidget(self.user_view)
