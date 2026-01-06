import re
import math
from typing import List, Dict,Optional, Set

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsItem, QGraphicsTextItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QRadioButton, QButtonGroup, QLabel, QInputDialog, QMessageBox,
    QToolBox, QDialog, QDialogButtonBox, QComboBox, QColorDialog
)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QFont, QIcon, QPixmap
from PySide6.QtCore import QRectF, Qt


from ..layout_generator import (
    generate_round_table_set, generate_rect_table_set, generate_decor,
    apply_rotation_to_group,
    LOGICAL_WIDTH, LOGICAL_HEIGHT
)


COLORS = {
    "free": "#A5D6A7",
    "reserved": "#EF9A9A",
    "selected": "#FFF59D",
    "table": "#ECEFF1",
    "decor_screen": "#29B6F6",
    "decor_stage": "#FFA726",
    "decor_bar": "#AB47BC",
    "decor_generic": "#BDBDBD"
}


def get_next_id(prefix: str, existing_items: List) -> str:
    max_val = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)")
    for item in existing_items:
        match = pattern.match(item.id)
        if match:
            v = int(match.group(1))
            if v > max_val:
                max_val = v
        if item.parent_id:
            match_p = pattern.match(item.parent_id)
            if match_p:
                vp = int(match_p.group(1))
                if vp > max_val:
                    max_val = vp
    return f"{prefix}{max_val + 1}"


class MapItem:
    def __init__(self, item_id, x, y, item_type, w=30, h=30, parent_id=None, rotation=0, label="", zone_id="Z1"):
        self.id = item_id
        self.x = x
        self.y = y
        self.type = item_type
        self.w = w
        self.h = h
        self.parent_id = parent_id
        self.rotation = rotation
        self.label = label
        self.zone_id = zone_id

    def to_dict(self):
        return self.__dict__

class GraphicItemBase(QGraphicsItem):
    def __init__(self, data: MapItem):
        super().__init__()
        self.data = data
        self.setPos(data.x, data.y)
        self.setRotation(data.rotation)
        self.setTransformOriginPoint(data.w / 2, data.h / 2)

    def boundingRect(self):
        return QRectF(0, 0, self.data.w, self.data.h)

    def paint(self, p, o, w):
        pass


class GraphicSeat(GraphicItemBase):
    def __init__(self, data: MapItem, is_reserved=False, base_color="#A5D6A7"):
        super().__init__(data)
        self.is_reserved = is_reserved
        self.is_selected = False
        self.base_color = base_color

        self.visual_rect = QGraphicsRectItem(0, 0, data.w, data.h, self)
        self.visual_rect.setPen(QPen(Qt.black))
        self.update_color()

        font = QFont()
        font.setPixelSize(10)
        if len(str(data.id)) > 4:
            font.setPixelSize(8)

        self.text = QGraphicsTextItem(str(data.id), self)
        self.text.setFont(font)
        br = self.text.boundingRect()
        self.text.setPos((data.w - br.width()) / 2, (data.h - br.height()) / 2)

        self.visual_rect.setAcceptedMouseButtons(Qt.NoButton)
        self.text.setAcceptedMouseButtons(Qt.NoButton)

    def update_color(self):
        if self.is_reserved:
            c = COLORS["reserved"]
        elif self.is_selected or self.isSelected():
            c = COLORS["selected"]
        else:
            c = self.base_color
        self.visual_rect.setBrush(QBrush(QColor(c)))

    def mousePressEvent(self, event):
        if self.is_reserved:
            return

        selectable = bool(self.flags() & QGraphicsItem.ItemIsSelectable)
        movable = bool(self.flags() & QGraphicsItem.ItemIsMovable)

        if selectable and not movable:
            self.is_selected = not self.is_selected
            self.update_color()

        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update_color()
        return super().itemChange(change, value)


class GraphicShape(GraphicItemBase):
    def __init__(self, data: MapItem):
        super().__init__(data)
        self.visual_item = None

        if data.type == "table_round":
            self.visual_item = QGraphicsEllipseItem(0, 0, data.w, data.h, self)
            color = COLORS["table"]
        elif data.type.startswith("decor_"):
            self.visual_item = QGraphicsRectItem(0, 0, data.w, data.h, self)
            color = COLORS.get(data.type, COLORS["decor_generic"])
        else:
            self.visual_item = QGraphicsRectItem(0, 0, data.w, data.h, self)
            color = COLORS["table"]

        self.visual_item.setBrush(QBrush(QColor(color)))
        self.visual_item.setPen(QPen(Qt.black))

        txt = data.label if data.type.startswith("decor_") else data.id
        self.text = QGraphicsTextItem(txt, self)
        br = self.text.boundingRect()
        self.text.setPos((data.w - br.width()) / 2, (data.h - br.height()) / 2)

        self.visual_item.setAcceptedMouseButtons(Qt.NoButton)
        self.text.setAcceptedMouseButtons(Qt.NoButton)


class GhostItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.w = 30
        self.h = 30
        self.tool_type = "seat"
        self.seats = 0
        self.is_square = False
        self.setOpacity(0.6)
        self.setZValue(200)

    def boundingRect(self):
        margin = 100
        return QRectF(-margin, -margin, self.w + margin * 2, self.h + margin * 2)

    def paint(self, painter, option, widget):
        painter.setPen(QPen(Qt.DashLine))
        painter.setBrush(QBrush(QColor(200, 200, 200, 150)))

        if self.tool_type == "table_round":
            painter.drawEllipse(0, 0, self.w, self.h)
        else:
            painter.drawRect(0, 0, self.w, self.h)

        if self.seats > 0:
            painter.setBrush(QBrush(QColor(165, 214, 167, 150)))
            painter.setPen(QPen(Qt.black))
            cx = self.w / 2
            cy = self.h / 2

            if self.tool_type == "table_round":
                radius = self.w / 2
                dist = radius + 20
                for i in range(self.seats):
                    angle = (2 * math.pi / self.seats) * i
                    sx = cx + math.cos(angle) * dist
                    sy = cy + math.sin(angle) * dist
                    painter.drawRect(sx - 15, sy - 15, 30, 30)

            elif self.tool_type == "table_rect":
                spacing = self.w / (math.ceil(self.seats / 2) + 1)
                for i in range(math.ceil(self.seats / 2)):
                    sx = spacing * (i + 1) - 15
                    if (i + 1) <= self.seats:
                        painter.drawRect(sx, -32, 30, 30)
                for i in range(math.ceil(self.seats / 2)):
                    sx = spacing * (i + 1) - 15
                    if (math.ceil(self.seats / 2) + i + 1) <= self.seats:
                        painter.drawRect(sx, self.h + 2, 30, 30)

    def update_config(self, cfg):
        mode = cfg.get("mode", "add_seat")
        self.seats = cfg.get("seats", 0)
        self.is_square = cfg.get("is_square", False)

        if mode == "add_table_round":
            self.tool_type = "table_round"
            radius = max(25, 5 + (self.seats * 4)) * 2
            self.w = self.h = radius
        elif mode == "add_table_rect":
            self.tool_type = "table_rect"
            side_seats = math.ceil(self.seats / 2)
            self.w = max(50, side_seats * 35 + 10) if self.is_square else max(70, side_seats * 35 + 20)
            self.h = self.w if self.is_square else 60
        elif mode == "add_decor":
            self.tool_type = "rect"
            self.w = cfg.get("w", 100)
            self.h = cfg.get("h", 50)
        else:
            self.tool_type = "rect"
            self.w = 30
            self.h = 30

        self.prepareGeometryChange()
        self.setTransformOriginPoint(self.w / 2, self.h / 2)
        self.update()


class InteractiveMapScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = "view"
        self.config = {}
        self.current_rotation = 0
        self.ghost = GhostItem()
        self.addItem(self.ghost)
        self.ghost.hide()

        self.border = QGraphicsRectItem(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
        self.border.setPen(QPen(Qt.black, 2))
        self.border.setZValue(-100)
        self.addItem(self.border)

    def set_tool(self, mode, config=None):
        self.mode = mode
        self.config = config or {}
        self.current_rotation = 0
        self.ghost.setRotation(0)
        if mode == "view" or mode == "delete":
            self.ghost.hide()
        else:
            full_cfg = self.config.copy()
            full_cfg["mode"] = mode
            self.ghost.update_config(full_cfg)
            self.ghost.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.current_rotation = (self.current_rotation + 45) % 360
            self.ghost.setRotation(self.current_rotation)
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode not in ["view", "delete"]:
            pos = event.scenePos()
            self.ghost.setPos(pos.x() - self.ghost.w / 2, pos.y() - self.ghost.h / 2)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.mode == "view":
            super().mousePressEvent(event)
            return

        pos = event.scenePos()
        cx, cy = pos.x(), pos.y()

        if not (0 <= cx <= LOGICAL_WIDTH and 0 <= cy <= LOGICAL_HEIGHT):
            return

        tl_x = pos.x() - self.ghost.w / 2
        tl_y = pos.y() - self.ghost.h / 2
        new_items = []
        current_model = self.parent().model
        zid = str(self.config.get("zone_id") or "Z1").strip() or "Z1"

        if self.mode == "add_seat":
            next_id = get_next_id("S", current_model)
            new_items.append({"id": next_id, "type": "seat", "x": tl_x, "y": tl_y, "w": 30, "h": 30, "rotation": 0, "zone_id": zid})
        elif self.mode == "add_decor":
            t = self.config.get("decor_type", "decor_generic")
            l = self.config.get("label", "Decor")
            w = self.config.get("w", 100)
            h = self.config.get("h", 50)
            next_id_label = get_next_id(l, current_model)
            new_items = generate_decor(cx, cy, t, w, h, l)
            new_items[0]["id"] = f"D-{next_id_label}"
        elif self.mode == "add_table_round":
            s = self.config.get("seats", 4)
            next_id = get_next_id("M", current_model)
            new_items = generate_round_table_set(cx, cy, next_id, s)
        elif self.mode == "add_table_rect":
            s = self.config.get("seats", 6)
            is_sq = self.config.get("is_square", False)
            next_id = get_next_id("M", current_model)
            new_items = generate_rect_table_set(cx, cy, next_id, s, is_sq)
        elif self.mode == "delete":
            item = self.itemAt(pos, self.views()[0].transform())
            target = None
            if isinstance(item, (GraphicSeat, GraphicShape)):
                target = item
            elif item and item.parentItem() and isinstance(item.parentItem(), (GraphicSeat, GraphicShape)):
                target = item.parentItem()
            elif item and item.parentItem() and item.parentItem().parentItem():
                target = item.parentItem().parentItem()
            if target:
                self.parent().remove_item(target.data)
                return
            
        for d in new_items:
            if d.get("type") == "seat" and not d.get("zone_id"):
                d["zone_id"] = zid

        new_items = apply_rotation_to_group(new_items, cx, cy, self.current_rotation)
        for d in new_items:
            zone_for_item = d.get("zone_id", "Z1") if d.get("type") == "seat" else ""
            mi = MapItem(
                d["id"], d["x"], d["y"], d["type"],
                d.get("w", 30), d.get("h", 30),
                d.get("parent_id"), d.get("rotation", 0),
                d.get("label", ""), zone_for_item
            )
            self.parent().add_item(mi)
        super().mousePressEvent(event)


class SeatMapView(QGraphicsView):
    def __init__(self, layout_data=None, reserved_seats=None, parent=None, editable=False, zones=None):
        super().__init__(parent)
        self.scene = InteractiveMapScene(self)
        self.setScene(self.scene)

        self.scene.setSceneRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMouseTracking(True)
        if editable:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setRubberBandSelectionMode(Qt.IntersectsItemShape)

        self.editable = editable
        self.model = []
        self.setFocusPolicy(Qt.StrongFocus)

        raw_res = reserved_seats or set()
        self._reserved_seats = {str(s).strip().upper() for s in raw_res}
        self._zones = zones or []

        self._zone_colors = {}
        for z in self._zones:
            zid = str(z.get("id") or "").strip()
            col = str(z.get("color") or "").strip()
            if zid and col:
                self._zone_colors[zid] = col

        self._zone_meta = {}
        for z in self._zones:
            zid = str(z.get("id") or "").strip()
            name = str(z.get("name") or zid).strip()
            try:
                price = float(z.get("price", 0))
            except Exception:
                price = 0.0
            if zid:
                self._zone_meta[zid] = (name, price)

        if layout_data:
            self.load_data(layout_data)

    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def load_data(self, data_list):
        self.scene.clear()

        self.scene.border = QGraphicsRectItem(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
        self.scene.border.setPen(QPen(Qt.black, 2))
        self.scene.border.setZValue(-100)
        self.scene.addItem(self.scene.border)

        self.scene.ghost = GhostItem()
        self.scene.addItem(self.scene.ghost)
        self.scene.ghost.hide()

        self.model = []
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        if not data_list:
            return

        for d in data_list:
            zid = d.get("zone_id", "Z1") if d.get("type") == "seat" else ""
            mi = MapItem(d["id"], d["x"], d["y"], d["type"], d.get("w", 30), d.get("h", 30),
                         d.get("parent_id"), d.get("rotation", 0), d.get("label", ""), zid)
            self.model.append(mi)
            self._draw(mi)

    def _draw(self, item: MapItem):
        gfx = None

        if item.type == "seat":
            cid = str(item.id).strip().upper()
            res = cid in self._reserved_seats
            base = self._zone_colors.get(item.zone_id, COLORS["free"])
            gfx = GraphicSeat(item, res, base)

            meta = self._zone_meta.get(item.zone_id)
            if meta:
                n, p = meta
                gfx.setToolTip(f"{item.id}\nZona: {n} ({item.zone_id})\nPret: {p:.2f} lei")
            else:
                gfx.setToolTip(str(item.id))


            if self.editable:
                gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
                gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
            else:
                if not res:
                    gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)

        else:
            gfx = GraphicShape(item)
            if self.editable:
                gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
                gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)

        if gfx:
            self.scene.addItem(gfx)


    def add_item(self, item):
        self.model.append(item)
        self._draw(item)

    def remove_item(self, item_data):
        ids = {item_data.id}
        for x in self.model:
            if x.parent_id == item_data.id:
                ids.add(x.id)
        self.model = [x for x in self.model if x.id not in ids and x.parent_id not in ids]
        self.load_data([x.to_dict() for x in self.model])

    def get_layout_data(self):
        layout = []

        for item in self.scene.items():
            if isinstance(item, (GraphicSeat, GraphicShape)):
                data = item.data  # MapItem

                pos = item.pos()
                data.x = pos.x()
                data.y = pos.y()

                data.rotation = item.rotation()

                layout.append(data.to_dict())

        return layout


    def get_selected_seats(self):
        return [i.data.id for i in self.scene.items() if isinstance(i, GraphicSeat) and i.is_selected]

    def set_mode(self, mode, config=None):
        self.scene.set_tool(mode, config)
