# ui/seatmap_view.py

from typing import List, Set

from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QDialog,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter
from PySide6.QtCore import QRectF, Qt

from services import hall_service, booking_service


class SeatItem(QGraphicsRectItem):
    def __init__(self, code: str, rect: QRectF, is_reserved: bool = False, parent=None) -> None:
        super().__init__(rect, parent)
        self.code = code
        self.is_reserved = is_reserved
        self.selected = False

        self.setPen(QPen(Qt.black))

        if self.is_reserved:
            self.setBrush(QBrush(QColor("#EF9A9A")))
            self.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        else:
            self.setBrush(QBrush(QColor("#A5D6A7")))
            self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)

    def mousePressEvent(self, event) -> None:
        if self.is_reserved:
            return

        self.selected = not self.selected
        if self.selected:
            self.setBrush(QBrush(QColor("#FFF59D")))
        else:
            self.setBrush(QBrush(QColor("#A5D6A7")))

        super().mousePressEvent(event)


class SeatMapView(QGraphicsView):
    def __init__(
        self,
        rows: int,
        cols: int,
        reserved_seats: Set[str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        if reserved_seats is None:
            reserved_seats = set()
        self._reserved_seats = {s.strip().upper() for s in reserved_seats}

        self._rows = rows
        self._cols = cols
        self._items: List[SeatItem] = []

        scene = QGraphicsScene(self)
        self.setScene(scene)

        seat_size = 24
        gap = 6

        for r in range(rows):
            for c in range(cols):
                x = c * (seat_size + gap)
                y = r * (seat_size + gap)
                rect = QRectF(x, y, seat_size, seat_size)

                row_letter = chr(ord("A") + r)
                code = f"{row_letter}{c + 1}"

                is_reserved = code.upper() in self._reserved_seats
                item = SeatItem(code, rect, is_reserved=is_reserved)
                scene.addItem(item)
                self._items.append(item)

        scene.setSceneRect(
            -10,
            -10,
            cols * (seat_size + gap) + 20,
            rows * (seat_size + gap) + 20,
        )

        self.setRenderHint(QPainter.Antialiasing, True)

    def get_selected_seats(self) -> List[str]:
        return [item.code for item in self._items if item.selected and not item.is_reserved]


class SeatSelectionDialog(QDialog):

    def __init__(self, event: dict, parent=None) -> None:
        super().__init__(parent)

        self._event = event

        self.setWindowTitle("Selectare locuri")

        layout = QVBoxLayout(self)

        from services.event_service import get_event

        event_full = get_event(event["id"])
        if event_full is None:
            hall_info = None
        else:
            hall_info = hall_service.get_hall(event_full["hall_id"])

        if hall_info is None:
            rows, cols = 8, 10
            hall_name = "Necunoscută"
        else:
            layout_cfg = hall_info.get("layout", {})
            rows = layout_cfg.get("rows", 8)
            cols = layout_cfg.get("cols", 10)
            hall_name = hall_info.get("name", "Necunoscută")

        bookings = booking_service.list_bookings_for_event(event["id"])
        reserved_seats: Set[str] = set()
        for b in bookings:
            for s in b.get("seats", []):
                reserved_seats.add(str(s).strip().upper())

        info_label = QLabel(
            f"Eveniment: <b>{event['title']}</b><br>"
            f"Data: {event['date']} {event['time']}<br>"
            f"Sală: {hall_name}<br>"
            f"<span style='color:#EF9A9A;'>Roșu</span> = ocupat, "
            f"<span style='color:#A5D6A7;'>verde</span> = liber, "
            f"<span style='color:#FFF59D;'>galben</span> = selectat."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.seat_map = SeatMapView(rows, cols, reserved_seats, self)
        layout.addWidget(self.seat_map)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_selected_seats(self) -> List[str]:
        return self.seat_map.get_selected_seats()
