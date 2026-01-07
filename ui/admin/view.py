from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QTableView, QMessageBox, QDialog, QHeaderView, QLineEdit,
    QStyledItemDelegate, QStyleOptionViewItem 
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen 
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel

from services import event_service, hall_service
from .models import EventsTableModel
from .dialogs import EventDialog, BookingsDialog, HallsDialog

class OccupancyDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        if index.column() != 4:
            super().paint(painter, option, index)
            return

        painter.save()

        ratio = index.data(Qt.UserRole)
        if ratio is None: ratio = 0.0
        rect = option.rect
        rect.adjust(4, 4, -4, -4)

        painter.setPen(Qt.NoPen) 
        painter.setBrush(QBrush(QColor("#e0e0e0")))
        painter.drawRoundedRect(rect, 4, 4) 

        full_width = rect.width()
        fill_width = int(full_width * ratio)

        if ratio < 0.5:
            color = QColor("#66bb6a") 
        elif ratio < 0.8:
            color = QColor("#ffa726") 
        else:
            color = QColor("#ef5350") 

        if fill_width > 0:
            painter.setBrush(QBrush(color))
            fill_rect = list(rect.getRect()) 
            fill_rect[2] = fill_width       
            painter.drawRoundedRect(fill_rect[0], fill_rect[1], fill_width, fill_rect[3], 4, 4)

        text_str = f"{int(ratio * 100)}%"
        painter.setPen(QColor("#000000")) 
        painter.drawText(option.rect, Qt.AlignCenter, text_str)

        painter.restore()

class EventFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def set_filter_text(self, text: str):
        self.filter_text = text.lower()
        self.invalidateFilter() 

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_text:
            return True 

        model = self.sourceModel()
        idx_title = model.index(source_row, 0, source_parent)
        idx_hall = model.index(source_row, 3, source_parent)
        
        title = str(model.data(idx_title, Qt.DisplayRole) or "").lower()
        hall_name = str(model.data(idx_hall, Qt.DisplayRole) or "").lower()

        return (self.filter_text in title) or (self.filter_text in hall_name)

class AdminEventsView(QWidget):
    back_to_login = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        title_label = QLabel("Panou Admin - Evenimente")
        title_label.setObjectName("TitleLabel") 
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cauta:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cauta dupa titlu sau sala...")
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

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
        self._source_model = EventsTableModel(self._events, self) 
        self._proxy_model = EventFilterProxyModel(self)           
        self._proxy_model.setSourceModel(self._source_model)      

        self.table_view.setModel(self._proxy_model)               
        self.table_view.setItemDelegateForColumn(4, OccupancyDelegate(self.table_view))

        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.search_edit.textChanged.connect(self.on_search_changed)

        self.refresh_events()

        self.add_button.clicked.connect(self.on_add_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.view_bookings_button.clicked.connect(self.on_view_bookings_clicked)
        self.manage_halls_button.clicked.connect(self.on_manage_halls_clicked)
        self.back_button.clicked.connect(self.back_to_login.emit)

    def refresh_events(self) -> None:
        self._source_model.set_events(event_service.list_events())

    def on_search_changed(self, text):
        self._proxy_model.set_filter_text(text)

    def get_selected_event(self) -> Optional[Dict]:
        proxy_idx = self.table_view.currentIndex()
        if not proxy_idx.isValid(): 
            return None
        
        source_idx = self._proxy_model.mapToSource(proxy_idx)
        return self._source_model.get_event_at_row(source_idx.row())

    def on_add_clicked(self) -> None:
        halls = hall_service.get_all_halls()
        if not halls:
            QMessageBox.warning(self, "Eroare", "Nu exista nicio sala definita.")
            return
        dialog = EventDialog(halls, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            event_service.create_event(data["title"], data["description"], data["date"], data["time"], data["hall_id"])
            self.refresh_events()

    def on_edit_clicked(self) -> None:
        event = self.get_selected_event()
        if not event: return
        halls = hall_service.get_all_halls()
        dialog = EventDialog(halls, event=event, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            event_service.update_event(event["id"], data["title"], data["description"], data["date"], data["time"], data["hall_id"])
            self.refresh_events()

    def on_delete_clicked(self) -> None:
        event = self.get_selected_event()
        if event and QMessageBox.question(self, "Stergere", f"Stergi evenimentul '{event['title']}'?") == QMessageBox.Yes:
            event_service.delete_event(event["id"])
            self.refresh_events()

    def on_view_bookings_clicked(self) -> None:
        event = self.get_selected_event()
        if event:
            BookingsDialog(event, parent=self).exec()

    def on_manage_halls_clicked(self) -> None:
        HallsDialog(parent=self).exec()
        self.refresh_events()