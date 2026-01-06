from typing import Dict

from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from .seatmap_core import SeatMapView

class SeatSelectionDialog(QDialog):
    def __init__(self, event: Dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Rezervare - {event['title']}")
        self.resize(1200, 800)
        layout = QVBoxLayout(self)

        from services import hall_service, booking_service
        hall = hall_service.get_hall(event['hall_id'])
        bookings = booking_service.list_bookings_for_event(event['id'])

        res = set()
        for b in bookings:
            for s in b.get("seats", []):
                res.add(str(s))

        layout_blob = hall.get("layout", [])

        if isinstance(layout_blob, dict):
            l_data = layout_blob.get("items", [])
            zones = layout_blob.get("zones", [])
        else:
            l_data = layout_blob
            zones = hall.get("zones", [])
            
        self.mv = SeatMapView(l_data, reserved_seats=res, parent=self, editable=False, zones=zones)
        layout.addWidget(self.mv)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_selected_seats(self):
        return self.mv.get_selected_seats()
    
    