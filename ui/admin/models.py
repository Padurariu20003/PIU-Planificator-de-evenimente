from typing import List, Dict, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from services import booking_service, hall_service

class EventsTableModel(QAbstractTableModel):
    def __init__(self, events: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._events = events

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._events)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 5

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        event = self._events[index.row()]
        col = index.column()

        if col == 4:
            if role == Qt.DisplayRole:
                 return self.calculate_occupancy_text(event)
            elif role == Qt.UserRole: 
                 return self.calculate_occupancy_ratio(event)
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter

        if role == Qt.DisplayRole:
            if col == 0: return event["title"]
            if col == 1: return event["date"]
            if col == 2: return event["time"]
            if col == 3: return event["hall_name"]
        
        return None

    def calculate_occupancy_ratio(self, event) -> float:
        try:
            bookings = booking_service.list_bookings_for_event(event["id"])
            hall = hall_service.get_hall(event["hall_id"])
            if not hall: return 0.0
            
            occupied_seats = 0
            for b in bookings:
                occupied_seats += len(b.get("seats", []))
            
            total_seats = 0
            layout = hall.get("layout", [])
            
            items = []
            if isinstance(layout, list):
                items = layout
            elif isinstance(layout, dict):
                items = layout.get("items", [])
            
            total_seats = len([x for x in items if x.get("type") == "seat"])
            
            if total_seats == 0: return 0.0
            return occupied_seats / total_seats
        except Exception:
            return 0.0

    def calculate_occupancy_text(self, event) -> str:
        ratio = self.calculate_occupancy_ratio(event)
        return f"{int(ratio * 100)}%"

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        if orientation == Qt.Horizontal:
            headers = ["Titlu", "Data", "Ora", "Sala", "Grad Ocupare"]
            if section < len(headers): return headers[section]
        return None

    def set_events(self, events: List[Dict]) -> None:
        self.beginResetModel()
        self._events = events
        self.endResetModel()

    def get_event_at_row(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._events): return self._events[row]
        return None

class BookingsTableModel(QAbstractTableModel):
    def __init__(self, bookings: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._bookings = bookings

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._bookings)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 5

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole: return None
        booking = self._bookings[index.row()]
        col = index.column()
        if col == 0: return booking["name"]
        if col == 1: return booking["email"]
        if col == 2: return ", ".join(booking.get("seats", []))
        if col == 3: return booking["created_at"]
        if col == 4: return f"{booking.get('total_price', 0):.2f} lei"
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        if orientation == Qt.Horizontal:
            headers = ["Nume", "Email", "Locuri", "Creat la", "Total"]
            if section < len(headers): return headers[section]
        return None

class HallsTableModel(QAbstractTableModel):
    def __init__(self, halls: List[Dict], parent=None) -> None:
        super().__init__(parent)
        self._halls = halls

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._halls)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole: return None
        hall = self._halls[index.row()]
        layout_data = hall.get("layout", [])
        seat_count = 0
        if isinstance(layout_data, list):
            seat_count = len([c for c in layout_data if c.get("type") == "seat"])
        elif isinstance(layout_data, dict):
            items = layout_data.get("items", [])
            seat_count = len([c for c in items if c.get("type") == "seat"])

        if index.column() == 0: return hall["name"]
        if index.column() == 1: return f"{seat_count} locuri"
        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        if orientation == Qt.Horizontal:
            return "Sala" if section == 0 else "Capacitate"
        return None

    def set_halls(self, halls: List[Dict]) -> None:
        self.beginResetModel()
        self._halls = halls
        self.endResetModel()

    def get_hall_at_row(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._halls): return self._halls[row]
        return None