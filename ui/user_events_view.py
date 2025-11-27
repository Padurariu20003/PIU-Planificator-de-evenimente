from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QFormLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from services import event_service
from services import booking_service
from .admin_events_view import EventsTableModel  # folosim același model ca la admin


class BookingDialog(QDialog):
    def __init__(self, event: Dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Rezervare locuri")

        self._event = event

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.seats_edit = QLineEdit()

        self.seats_edit.setPlaceholderText("Ex: A1,A2,A3")

        event_label = QLabel(
            f"Eveniment: <b>{event['title']}</b> ({event['date']} {event['time']}, {event['hall_name']})"
        )
        event_label.setWordWrap(True)

        layout.addRow(event_label)
        layout.addRow("Nume:", self.name_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Locuri (ex. A1,A2):", self.seats_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

    def get_data(self) -> Dict:
        seats_raw = self.seats_edit.text()
        seats_list = [s.strip() for s in seats_raw.split(",") if s.strip()]
        return {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "seats": seats_list,
        }


class UserEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Listă evenimente - Utilizator")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Selectați un eveniment din listă și apăsați pe „Rezervă locuri” pentru a face o rezervare."
        )
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        self.table_view = QTableView()
        main_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        self.book_button = QPushButton("Rezervă locuri")
        self.refresh_button = QPushButton("Reîncarcă lista")
        self.back_button = QPushButton("Înapoi la login")

        button_layout.addWidget(self.book_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.back_button)

        main_layout.addLayout(button_layout)

        self._events: List[Dict] = []
        self._model = EventsTableModel(self._events, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        self.book_button.clicked.connect(self.on_book_clicked)
        self.refresh_button.clicked.connect(self.refresh_events)
        self.back_button.clicked.connect(self.back_to_login.emit)

        self.refresh_events()


    def refresh_events(self) -> None:
        events = event_service.list_events()
        self._model.set_events(events)

    def get_selected_event(self) -> Optional[Dict]:
        index = self.table_view.currentIndex()
        if not index.isValid():
            return None
        return self._model.get_event_at_row(index.row())


    def on_book_clicked(self) -> None:
        event = self.get_selected_event()
        if event is None:
            QMessageBox.information(
                self,
                "Informație",
                "Selectați mai întâi un eveniment din listă.",
            )
            return

        dialog = BookingDialog(event, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()
        if not data["name"] or not data["email"] or not data["seats"]:
            QMessageBox.warning(
                self,
                "Eroare",
                "Completați numele, emailul și cel puțin un loc.",
            )
            return

        try:
            booking_service.create_booking(
                event_id=event["id"],
                name=data["name"],
                email=data["email"],
                seats=data["seats"],
            )
        except ValueError as ex:
            QMessageBox.critical(
                self,
                "Rezervare eșuată",
                str(ex),
            )
            return

        QMessageBox.information(
            self,
            "Rezervare reușită",
            "Rezervarea a fost înregistrată cu succes.",
        )
