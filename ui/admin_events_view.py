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
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex

from services import event_service, hall_service


class EventsTableModel(QAbstractTableModel):

    def __init__(self, events: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._events = events

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._events)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 4  # titlu, data, ora, sala

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
                return "Sală"

        return None

    def set_events(self, events: List[Dict]) -> None:
        self.beginResetModel()
        self._events = events
        self.endResetModel()

    def get_event_at_row(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._events):
            return self._events[row]
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
        form_layout.addRow("Sală:", self.hall_combo)

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


class AdminEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title_label = QLabel("Panou Admin - Evenimente")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # tabelul cu evenimente
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # butoane
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.back_button = QPushButton("Back to Login")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
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
                self, "Eroare", "Nu există nicio sală definită. Verificați baza de date."
            )
            return

        dialog = EventDialog(halls, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["title"] or not data["date"] or not data["time"]:
                QMessageBox.warning(
                    self, "Eroare", "Titlul, data și ora sunt obligatorii."
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
                self, "Informație", "Selectați mai întâi un eveniment din listă."
            )
            return

        halls = hall_service.get_all_halls()
        dialog = EventDialog(halls, event=event, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["title"] or not data["date"] or not data["time"]:
                QMessageBox.warning(
                    self, "Eroare", "Titlul, data și ora sunt obligatorii."
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
                self, "Informație", "Selectați mai întâi un eveniment din listă."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmare ștergere",
            f"Sigur doriți să ștergeți evenimentul '{event['title']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event_service.delete_event(event["id"])
            self.refresh_events()
