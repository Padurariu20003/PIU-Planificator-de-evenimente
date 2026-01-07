from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, 
    QTableView, QPushButton, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from services import event_service, booking_service
from core import session
from ..admin.models import EventsTableModel
from ..common import OccupancyDelegate, EventFilterProxyModel
from .dialogs import BookingDialog, UserBookingsDialog

class UserEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Lista evenimente - Utilizator")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Selectati un eveniment din lista si apasati pe „Rezerva locuri” "
            "pentru a selecta locurile pe harta si a face o rezervare.\n"
            "Puteti vedea si „Rezervarile mele” facute cu email-ul dvs."
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cauta:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cauta dupa titlu sau sala...")
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)

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
        self._source_model = EventsTableModel(self._events, self)
        self._proxy_model = EventFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._source_model)

        self.table_view.setModel(self._proxy_model)
        self.table_view.setItemDelegateForColumn(4, OccupancyDelegate(self.table_view))
        
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.search_edit.textChanged.connect(self.on_search_changed)
        self.book_button.clicked.connect(self.on_book_clicked)
        self.refresh_button.clicked.connect(self.refresh_events)
        self.my_bookings_button.clicked.connect(self.on_my_bookings_clicked)
        self.back_button.clicked.connect(self.back_to_login.emit)

        self.refresh_events()

    def refresh_events(self) -> None:
        events = event_service.list_events()
        self._source_model.set_events(events)

    def on_search_changed(self, text):
        self._proxy_model.set_filter_text(text)

    def get_selected_event(self) -> Optional[Dict]:
        proxy_idx = self.table_view.currentIndex()
        if not proxy_idx.isValid(): return None
        source_idx = self._proxy_model.mapToSource(proxy_idx)
        return self._source_model.get_event_at_row(source_idx.row())

    def on_book_clicked(self) -> None:
        event = self.get_selected_event()
        if event is None:
            QMessageBox.information(self, "Informatie", "Selectati un eveniment.")
            return

        dialog = BookingDialog(event, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                booking_service.create_booking(event["id"], data["name"], data["email"], data["seats"])
                QMessageBox.information(self, "Succes", "Rezervare reusita!")
            except ValueError as ex:
                QMessageBox.warning(self, "Eroare", str(ex))

    def on_my_bookings_clicked(self) -> None:
        email, _ = session.get_current_user()
        if not email:
            QMessageBox.information(self, "Info", "Trebuie sa fiti autentificat cu email.")
            return
        
        if not booking_service.list_bookings_for_email(email):
             QMessageBox.information(self, "Info", "Nu aveti rezervari.")
             return

        UserBookingsDialog(email, parent=self).exec()