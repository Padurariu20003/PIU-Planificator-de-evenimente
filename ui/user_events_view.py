from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, Signal


class UserEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title_label = QLabel("Lista evenimente - Utilizator")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        info_label = QLabel(
            "Aici utilizatorul va vedea evenimentele si va putea sa isi rezerve locuri.\n"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()

        back_button = QPushButton("Inapoi la login")
        back_button.clicked.connect(self.back_to_login.emit)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        layout.addStretch()
