from typing import List, Dict
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

class MyBookingsTableModel(QAbstractTableModel):
    def __init__(self, bookings: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._bookings = bookings

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._bookings)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 6

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        booking = self._bookings[index.row()]
        col = index.column()

        if col == 0: return booking["event_title"]
        if col == 1: return f"{booking['event_date']} {booking['event_time']}"
        if col == 2: return booking["hall_name"]
        if col == 3: return ", ".join(booking.get("seats", []))
        if col == 4: return booking["created_at"]
        if col == 5: return f"{booking.get('total_price', 0):.2f} lei"
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        if orientation == Qt.Horizontal:
            headers = ["Eveniment", "Data/Ora", "Sala", "Locuri", "Creat la", "Total"]
            if section < len(headers): return headers[section]
        return None

    def set_bookings(self, bookings: List[Dict]) -> None:
        self.beginResetModel()
        self._bookings = bookings
        self.endResetModel()