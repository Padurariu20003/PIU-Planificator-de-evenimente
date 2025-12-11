import sys
from PySide6.QtWidgets import QApplication

from core.db import init_db
from services.auth_service import init_default_admin
from services.hall_service import init_default_halls
from ui.main_window import MainWindow


def main() -> None:

    init_db()
    init_default_admin()
    init_default_halls()

    app = QApplication(sys.argv)

    window = MainWindow()
    #window.show()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
