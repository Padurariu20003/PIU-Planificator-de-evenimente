from typing import Dict, List
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, 
    QDialogButtonBox, QMessageBox, QVBoxLayout, QTableView, QHeaderView, QApplication
)
from PySide6.QtCore import Qt

from core import session
from core.validators import validate_email
from services import hall_service, booking_service
from ui.seatmap import SeatSelectionDialog
from .models import MyBookingsTableModel

class BookingDialog(QDialog):
    def __init__(self, event: Dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rezervare locuri")
        
        screen = self.parent().screen() if self.parent() else QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.resize(int(rect.width() * 0.35), int(rect.height() * 0.30))

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

        current_email, _ = session.get_current_user()
        if current_email:
            self.email_edit.setText(current_email)
            self.email_edit.setReadOnly(True)

        self.seats_display = QLineEdit()
        self.seats_display.setReadOnly(True)
        self.seats_display.setPlaceholderText("Niciun loc selectat")

        self.total_label = QLabel("Total: 0.00 lei")
        layout.addRow("Total:", self.total_label)
        self.breakdown_label = QLabel("-")
        self.breakdown_label.setWordWrap(True)
        self.breakdown_label.setTextFormat(Qt.RichText) 

        layout.addRow("Detalii pe zone:", self.breakdown_label)

        self.select_seats_button = QPushButton("Selecteaza locuri...")

        layout.addRow("Nume:", self.name_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Locuri selectate:", self.seats_display)
        layout.addRow("", self.select_seats_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.select_seats_button.clicked.connect(self.on_select_seats_clicked)

    def on_select_seats_clicked(self) -> None:
        dialog = SeatSelectionDialog(self._event, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        seats = dialog.get_selected_seats()
        self.selected_seats = seats
        self.seats_display.setText(", ".join(seats))
        self._calculate_price(seats)

    def _calculate_price(self, seats):
        hall = hall_service.get_hall(self._event["hall_id"]) or {}
        layout_items = hall.get("layout", []) or []
        zones = hall.get("zones", []) or []

        zone_meta = {str(z.get("id")): {"price": float(z.get("price", 0)), "name": z.get("name"), "color": z.get("color")} for z in zones if z.get("id")}
        seat_to_zone = {str(it.get("id")): str(it.get("zone_id") or "Z1") for it in layout_items if it.get("type") == "seat"}

        counts = {}
        for sid in seats:
            zid = seat_to_zone.get(str(sid), "Z1")
            counts[zid] = counts.get(zid, 0) + 1

        lines = []
        total_calc = 0.0
        for zid, cnt in sorted(counts.items()):
            meta = zone_meta.get(zid, {"price": 0.0, "name": zid, "color": "#DDDDDD"})
            subtotal = meta["price"] * cnt
            total_calc += subtotal
            lines.append(f"<span style='background:{meta['color']};'>&nbsp;&nbsp;</span> <b>{zid}</b>: {cnt} x {meta['price']:.2f} = <b>{subtotal:.2f} lei</b>")

        self.breakdown_label.setText("<br>".join(lines) if lines else "-")
        self.total_label.setText(f"{total_calc:.2f} lei")

    def on_accept(self) -> None:
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        if not name or not email:
            QMessageBox.warning(self, "Eroare", "Completati toate campurile.")
            return
        try:
            email = validate_email(email)
        except ValueError as ex:
            QMessageBox.warning(self, "Eroare", str(ex))
            return
        if not self.selected_seats:
            QMessageBox.warning(self, "Eroare", "Selectati cel putin un loc.")
            return
        self.email_edit.setText(email)
        self.accept()

    def get_data(self) -> Dict:
        return {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "seats": list(self.selected_seats),
        }

class UserBookingsDialog(QDialog):
    def __init__(self, email: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rezervarile mele")
        
        screen = self.parent().screen() if self.parent() else QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.resize(int(rect.width() * 0.5), int(rect.height() * 0.5))

        layout = QVBoxLayout(self)
        info_label = QLabel(f"Rezervarile pentru contul:<br><b>{email}</b>")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        bookings = booking_service.list_bookings_for_email(email)
        self._model = MyBookingsTableModel(bookings, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)