from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit, 
    QComboBox, QMessageBox, QVBoxLayout, QLabel, QTableView, 
    QHBoxLayout, QPushButton, QHeaderView, QDateEdit, QTimeEdit
)
from PySide6.QtCore import Qt, QDate, QTime
from services import booking_service, hall_service
from .models import BookingsTableModel, HallsTableModel
from ..seatmap.seatmap_editor_widget import HallEditorWidget

class EventDialog(QDialog):
    def __init__(self, halls: List[Dict], event: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eveniment")
        self._halls = halls
        
        form_layout = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True) 
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(19, 30)) 

        self.hall_combo = QComboBox()
        for hall in halls:
            self.hall_combo.addItem(hall["name"], hall["id"])

        form_layout.addRow("Titlu:", self.title_edit)
        form_layout.addRow("Descriere:", self.description_edit)
        form_layout.addRow("Data:", self.date_edit)
        form_layout.addRow("Ora:", self.time_edit)
        form_layout.addRow("Sala:", self.hall_combo)

        if event is not None:
            self.title_edit.setText(event["title"])
            self.description_edit.setPlainText(event["description"])
            
            try:
                y, m, d = map(int, event["date"].split("-"))
                self.date_edit.setDate(QDate(y, m, d))
                hr, mn = map(int, event["time"].split(":"))
                self.time_edit.setTime(QTime(hr, mn))
            except:
                pass 

            for i in range(self.hall_combo.count()):
                if self.hall_combo.itemData(i) == event["hall_id"]:
                    self.hall_combo.setCurrentIndex(i)
                    break

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        form_layout.addRow(buttons)

    def on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Eroare", "Titlul este obligatoriu.")
            return
        self.accept()

    def get_data(self) -> Dict:
        return {
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_edit.time().toString("HH:mm"),
            "hall_id": self.hall_combo.currentData(),
        }

class BookingsDialog(QDialog):
    def __init__(self, event: Dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rezervari pentru eveniment")
        layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Rezervari: <b>{event['title']}</b>")
        layout.addWidget(info_label)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        bookings = booking_service.list_bookings_for_event(event["id"])
        self._model = BookingsTableModel(bookings, self)
        self.table_view.setModel(self._model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.close)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.close)
        layout.addWidget(buttons)

class HallDialog(QDialog):
    def __init__(self, hall: Optional[Dict] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurare sala")
        self.resize(1400, 900)
        self.setWindowState(self.windowState() | Qt.WindowMaximized)
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Nume sala:", self.name_edit)
        layout.addLayout(form_layout)

        current_layout = []
        if hall:
            self.name_edit.setText(hall["name"])
            raw_layout = hall.get("layout", [])
            if isinstance(raw_layout, list): current_layout = raw_layout

        self.zones = (hall.get("zones") if hall else None)
        self.editor = HallEditorWidget(current_layout, parent=self, zones=self.zones)
        layout.addWidget(self.editor)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> Dict:
        data = self.editor.get_data()
        return {
            "name": self.name_edit.text().strip(),
            "layout": data["items"],
            "zones": data["zones"],
        }

class HallsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Administrare sali")
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        btns = QHBoxLayout()
        self.add_btn = QPushButton("Adauga sala")
        self.edit_btn = QPushButton("Editeaza")
        self.del_btn = QPushButton("Sterge")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self._halls = []
        self._model = HallsTableModel(self._halls, self)
        self.table_view.setModel(self._model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)

        self.refresh_halls()

        self.add_btn.clicked.connect(self.on_add)
        self.edit_btn.clicked.connect(self.on_edit)
        self.del_btn.clicked.connect(self.on_delete)
        
        bbox = QDialogButtonBox(QDialogButtonBox.Close)
        bbox.rejected.connect(self.close)
        layout.addWidget(bbox)

    def refresh_halls(self):
        self._model.set_halls(hall_service.get_all_halls())

    def get_selected(self) -> Optional[Dict]:
        idx = self.table_view.currentIndex()
        if not idx.isValid(): return None
        return self._model.get_hall_at_row(idx.row())

    def on_add(self):
        d = HallDialog(parent=self)
        if d.exec() == QDialog.Accepted:
            data = d.get_data()
            try:
                hall_service.create_hall(data["name"], data["layout"], zones=data["zones"])
                self.refresh_halls()
            except Exception as e:
                QMessageBox.warning(self, "Eroare", str(e))

    def on_edit(self):
        hall = self.get_selected()
        if not hall: return
        d = HallDialog(hall, parent=self)
        if d.exec() == QDialog.Accepted:
            data = d.get_data()
            try:
                hall_service.update_hall(hall["id"], data["name"], data["layout"], zones=data["zones"])
                self.refresh_halls()
            except Exception as e:
                QMessageBox.warning(self, "Eroare", str(e))

    def on_delete(self):
        hall = self.get_selected()
        if hall and QMessageBox.question(self, "Confirmare", "Sigur stergeti sala?") == QMessageBox.Yes:
            hall_service.delete_hall(hall["id"])
            self.refresh_halls()