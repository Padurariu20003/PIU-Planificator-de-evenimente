from typing import List, Dict, Optional

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
    QTextEdit,
    QComboBox,
    QFormLayout,
    QMessageBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex

from services import event_service, hall_service, booking_service


class EventsTableModel(QAbstractTableModel):
    def __init__(self, events: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._events = events

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._events)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 4

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        event = self._events[index.row()]
        col = index.column()

        if col == 0:
            return event["title"]
        elif col == 1:
            return event["date"]
        elif col == 2:
            return event["time"]
        elif col == 3:
            return event["hall_name"]

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Titlu"
            if section == 1:
                return "Data"
            if section == 2:
                return "Ora"
            if section == 3:
                return "Sala"

        return None

    def set_events(self, events: List[Dict]) -> None:
        self.beginResetModel()
        self._events = events
        self.endResetModel()

    def get_event_at_row(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._events):
            return self._events[row]
        return None


class BookingsTableModel(QAbstractTableModel):
    def __init__(self, bookings: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._bookings = bookings

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._bookings)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 4

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        booking = self._bookings[index.row()]
        col = index.column()

        if col == 0:
            return booking["name"]
        elif col == 1:
            return booking["email"]
        elif col == 2:
            return ", ".join(booking.get("seats", []))
        elif col == 3:
            return booking["created_at"]

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Nume"
            if section == 1:
                return "Email"
            if section == 2:
                return "Locuri"
            if section == 3:
                return "Creat la"

        return None

    def set_bookings(self, bookings: List[Dict]) -> None:
        self.beginResetModel()
        self._bookings = bookings
        self.endResetModel()


class HallsTableModel(QAbstractTableModel):
    def __init__(self, halls: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._halls = halls

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._halls)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 3

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        hall = self._halls[index.row()]
        col = index.column()

        layout = hall.get("layout", {})
        rows = layout.get("rows", 0)
        cols = layout.get("cols", 0)

        if col == 0:
            return hall["name"]
        elif col == 1:
            return rows
        elif col == 2:
            return cols

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Sala"
            if section == 1:
                return "Randuri"
            if section == 2:
                return "Coloane"

        return None

    def set_halls(self, halls: List[Dict]) -> None:
        self.beginResetModel()
        self._halls = halls
        self.endResetModel()

    def get_hall_at_row(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._halls):
            return self._halls[row]
        return None


class EventDialog(QDialog):
    def __init__(self, halls: List[Dict], event: Optional[Dict] = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Eveniment")
        self._halls = halls
        self._event = event

        form_layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.date_edit = QLineEdit()
        self.time_edit = QLineEdit()
        self.hall_combo = QComboBox()

        for hall in halls:
            self.hall_combo.addItem(hall["name"], hall["id"])

        form_layout.addRow("Titlu:", self.title_edit)
        form_layout.addRow("Descriere:", self.description_edit)
        form_layout.addRow("Data (YYYY-MM-DD):", self.date_edit)
        form_layout.addRow("Ora (HH:MM):", self.time_edit)
        form_layout.addRow("Sala:", self.hall_combo)

        if event is not None:
            self.title_edit.setText(event["title"])
            self.description_edit.setPlainText(event["description"])
            self.date_edit.setText(event["date"])
            self.time_edit.setText(event["time"])

            for i in range(self.hall_combo.count()):
                if self.hall_combo.itemData(i) == event["hall_id"]:
                    self.hall_combo.setCurrentIndex(i)
                    break

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form_layout.addRow(buttons)

    def get_data(self) -> Dict:
        return {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "date": self.date_edit.text().strip(),
            "time": self.time_edit.text().strip(),
            "hall_id": self.hall_combo.currentData(),
        }


class BookingsDialog(QDialog):
    def __init__(self, event: Dict, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Rezervari pentru eveniment")

        layout = QVBoxLayout(self)

        info_label = QLabel(
            f"Rezervari pentru evenimentul:<br>"
            f"<b>{event['title']}</b> ({event['date']} {event['time']}, {event['hall_name']})"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        bookings = booking_service.list_bookings_for_event(event["id"])
        self._model = BookingsTableModel(bookings, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.close)

        layout.addWidget(buttons)


class HallDialog(QDialog):
    def __init__(self, hall: Optional[Dict] = None, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Sala")

        form_layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.rows_spin = QSpinBox()
        self.cols_spin = QSpinBox()

        self.rows_spin.setMinimum(1)
        self.rows_spin.setMaximum(100)
        self.cols_spin.setMinimum(1)
        self.cols_spin.setMaximum(100)

        form_layout.addRow("Nume sala:", self.name_edit)
        form_layout.addRow("Randuri:", self.rows_spin)
        form_layout.addRow("Coloane:", self.cols_spin)

        if hall is not None:
            self.name_edit.setText(hall["name"])
            layout = hall.get("layout", {})
            self.rows_spin.setValue(layout.get("rows", 10))
            self.cols_spin.setValue(layout.get("cols", 10))

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form_layout.addRow(buttons)

    def get_data(self) -> Dict:
        return {
            "name": self.name_edit.text().strip(),
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
        }


class HallsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Administrare sali")

        layout = QVBoxLayout(self)

        info_label = QLabel(
            "Administrati salile disponibile pentru evenimente.\n"
            "Modificarea layout-ului unei sali va afecta afisarea locurilor pentru evenimentele asociate."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Adauga sala")
        self.edit_button = QPushButton("Editeaza sala")
        self.delete_button = QPushButton("Sterge sala")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        self._halls: List[Dict] = []
        self._model = HallsTableModel(self._halls, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        self.refresh_halls()

        self.add_button.clicked.connect(self.on_add_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        close_buttons.rejected.connect(self.reject)
        close_buttons.accepted.connect(self.accept)
        close_buttons.button(QDialogButtonBox.Close).clicked.connect(self.close)
        layout.addWidget(close_buttons)

    def refresh_halls(self) -> None:
        halls = hall_service.get_all_halls()
        self._model.set_halls(halls)

    def get_selected_hall(self) -> Optional[Dict]:
        index = self.table_view.currentIndex()
        if not index.isValid():
            return None
        return self._model.get_hall_at_row(index.row())

    def on_add_clicked(self) -> None:
        dialog = HallDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                hall_service.create_hall(data["name"], data["rows"], data["cols"])
            except ValueError as ex:
                QMessageBox.warning(self, "Eroare", str(ex))
                return
            self.refresh_halls()

    def on_edit_clicked(self) -> None:
        hall = self.get_selected_hall()
        if hall is None:
            QMessageBox.information(
                self, "Informatii", "Selectati mai intai o sala din lista."
            )
            return

        dialog = HallDialog(hall=hall, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                hall_service.update_hall(
                    hall_id=hall["id"],
                    name=data["name"],
                    rows=data["rows"],
                    cols=data["cols"],
                )
            except ValueError as ex:
                QMessageBox.warning(self, "Eroare", str(ex))
                return
            self.refresh_halls()

    def on_delete_clicked(self) -> None:
        hall = self.get_selected_hall()
        if hall is None:
            QMessageBox.information(
                self, "Informatii", "Selectati mai intai o sala din lista."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmare stergere",
            "Stergerea unei sali va sterge si evenimentele si rezervarile asociate.\n"
            f"Sigur doriti sa stergeti sala '{hall['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            hall_service.delete_hall(hall["id"])
            self.refresh_halls()


class AdminEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title_label = QLabel("Panou Admin - Evenimente")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Adauga eveniment")
        self.edit_button = QPushButton("Editeaza")
        self.delete_button = QPushButton("Sterge")
        self.view_bookings_button = QPushButton("Vezi rezervari")
        self.manage_halls_button = QPushButton("Administreaza sali")
        self.back_button = QPushButton("Inapoi la login")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.view_bookings_button)
        button_layout.addWidget(self.manage_halls_button)
        button_layout.addStretch()
        button_layout.addWidget(self.back_button)

        layout.addLayout(button_layout)

        self._events: List[Dict] = []
        self._model = EventsTableModel(self._events, self)
        self.table_view.setModel(self._model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)

        self.refresh_events()

        self.add_button.clicked.connect(self.on_add_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.view_bookings_button.clicked.connect(self.on_view_bookings_clicked)
        self.manage_halls_button.clicked.connect(self.on_manage_halls_clicked)
        self.back_button.clicked.connect(self.back_to_login.emit)

    def refresh_events(self) -> None:
        events = event_service.list_events()
        self._model.set_events(events)

    def get_selected_event(self) -> Optional[Dict]:
        index = self.table_view.currentIndex()
        if not index.isValid():
            return None
        return self._model.get_event_at_row(index.row())

    def on_add_clicked(self) -> None:
        halls = hall_service.get_all_halls()
        if not halls:
            QMessageBox.warning(
                self, "Eroare", "Nu exista nicio sala definita. Verificati baza de date."
            )
            return

        dialog = EventDialog(halls, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["title"] or not data["date"] or not data["time"]:
                QMessageBox.warning(
                    self, "Eroare", "Titlul, data si ora sunt obligatorii."
                )
                return

            event_service.create_event(
                data["title"],
                data["description"],
                data["date"],
                data["time"],
                data["hall_id"],
            )
            self.refresh_events()

    def on_edit_clicked(self) -> None:
        event = self.get_selected_event()
        if event is None:
            QMessageBox.information(
                self, "Informatii", "Selectati mai intai un eveniment din lista."
            )
            return

        halls = hall_service.get_all_halls()
        dialog = EventDialog(halls, event=event, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["title"] or not data["date"] or not data["time"]:
                QMessageBox.warning(
                    self, "Eroare", "Titlul, data si ora sunt obligatorii."
                )
                return

            event_service.update_event(
                event["id"],
                data["title"],
                data["description"],
                data["date"],
                data["time"],
                data["hall_id"],
            )
            self.refresh_events()

    def on_delete_clicked(self) -> None:
        event = self.get_selected_event()
        if event is None:
            QMessageBox.information(
                self, "Informatii", "Selectati mai intai un eveniment din lista."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmare stergere",
            f"Sigur doriti sa stergeti evenimentul '{event['title']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event_service.delete_event(event["id"])
            self.refresh_events()

    def on_view_bookings_clicked(self) -> None:
        event = self.get_selected_event()
        if event is None:
            QMessageBox.information(
                self,
                "Informatii",
                "Selectati mai intai un eveniment din lista.",
            )
            return

        dialog = BookingsDialog(event, parent=self)
        dialog.exec()

    def on_manage_halls_clicked(self) -> None:
        dialog = HallsDialog(parent=self)
        dialog.exec()
        self.refresh_events()
