from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QSortFilterProxyModel

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
            color = QColor("#66bb6a") # Verde
        elif ratio < 0.8:
            color = QColor("#ffa726") # Portocaliu
        else:
            color = QColor("#ef5350") # Rosu

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