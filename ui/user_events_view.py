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
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex

from services import event_service, booking_service
from .admin_events_view import EventsTableModel
from .seatmap_view import SeatSelectionDialog
from core import session


class BookingDialog(QDialog):
    def __init__(self, event: Dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Rezervare locuri")

        self._event = event
        self.selected_seats: List[str] = []

        layout = QFormLayout(self)

        event_label = QLabel(
            f"Eveniment: <b>{event['title']}</b> "
            f"({event['date']} {event['time']}, {event['hall_name']})"
        )
        event_label.setWordWrap(True)

        layout.addRow(event_label)

        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()

        self.seats_display = QLineEdit()
        self.seats_display.setReadOnly(True)
        self.seats_display.setPlaceholderText("Niciun loc selectat")

        self.select_seats_button = QPushButton("Selecteaza locuri...")

        layout.addRow("Nume:", self.name_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Locuri selectate:", self.seats_display)
        layout.addRow("", self.select_seats_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        self.select_seats_button.clicked.connect(self.on_select_seats_clicked)

    def on_select_seats_clicked(self) -> None:
        dialog = SeatSelectionDialog(self._event, parent=self)
        if dialog.exec() == QDialog.Accepted:
            seats = dialog.get_selected_seats()
            if not seats:
                QMessageBox.warning(
                    self,
                    "Atentie",
                    "Nu ati selectat niciun loc.",
                )
                return

            self.selected_seats = seats
            self.seats_display.setText(", ".join(seats))

    def get_data(self) -> Dict:
        return {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "seats": self.selected_seats,
        }


class MyBookingsTableModel(QAbstractTableModel):
    def __init__(self, bookings: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._bookings = bookings

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._bookings)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 5

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        booking = self._bookings[index.row()]
        col = index.column()

        if col == 0:
            return booking["event_title"]
        elif col == 1:
            return f"{booking['event_date']} {booking['event_time']}"
        elif col == 2:
            return booking["hall_name"]
        elif col == 3:
            return ", ".join(booking.get("seats", []))
        elif col == 4:
            return booking["created_at"]

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Eveniment"
            if section == 1:
                return "Data/Ora"
            if section == 2:
                return "Sală"
            if section == 3:
                return "Locuri"
            if section == 4:
                return "Creat la"

        return None

    def set_bookings(self, bookings: List[Dict]) -> None:
        self.beginResetModel()
        self._bookings = bookings
        self.endResetModel()


class UserBookingsDialog(QDialog):
    def __init__(self, email: str, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Rezervarile mele")

        layout = QVBoxLayout(self)

        info_label = QLabel(
            f"Rezervarile pentru contul:<br><b>{email}</b>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        bookings = booking_service.list_bookings_for_email(email)
        self._model = MyBookingsTableModel(bookings, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.close)

        layout.addWidget(buttons)


class UserEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Lista evenimente - Utilizator")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Selectati un eveniment din lista si apasasi pe „Rezerva locuri” "
            "pentru a selecta locurile pe harta si a face o rezervare.\n"
            "Puteti vedea si „Rezervarile mele” facute cu email-ul dvs."
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        self.table_view = QTableView()
        main_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        self.book_button = QPushButton("Rezerva locuri")
        self.refresh_button = QPushButton("Reincarca lista")
        self.my_bookings_button = QPushButton("Rezervarile mele")
        self.back_button = QPushButton("Inapoi la login")

        button_layout.addWidget(self.book_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.my_bookings_button)
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
        self.my_bookings_button.clicked.connect(self.on_my_bookings_clicked)
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
                "Informatie",
                "Selectati mai intai un eveniment din lista.",
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
                "Completati numele, emailul si selectati cel putin un loc.",
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
                "Rezervare esuata",
                str(ex),
            )
            return

        QMessageBox.information(
            self,
            "Rezervare reusita",
            "Rezervarea a fost inregistrata cu succes.",
        )

    def on_my_bookings_clicked(self) -> None:
        email, role = session.get_current_user()
        if not email:
            QMessageBox.information(
                self,
                "Informatie",
                "Functia „Rezervarile mele” este disponibila doar pentru "
                "utilizatorii autentificati cu email.\n"
                "Creati un cont prin „Inregistreaza-te” si autentificati-va.",
            )
            return

        bookings = booking_service.list_bookings_for_email(email)
        if not bookings:
            QMessageBox.information(
                self,
                "Rezervarile mele",
                "Nu aveti nicio rezervare inregistrata cu acest email.",
            )
            return

        dialog = UserBookingsDialog(email, parent=self)
        dialog.exec()
