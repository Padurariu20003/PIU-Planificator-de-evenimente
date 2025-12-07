import uuid
import re
import math
from typing import List, Dict, Optional, Set

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsItem, QGraphicsTextItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QRadioButton, QButtonGroup, QLabel, QInputDialog, QMessageBox,
    QToolBox, QDialog, QDialogButtonBox
)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QFont
from PySide6.QtCore import QRectF, Qt

# Importam generatoarele
from .layout_generator import (
    generate_round_table_set, generate_rect_table_set, generate_decor,
    center_layout, apply_rotation_to_group,
    create_cinema_template, create_wedding_template, create_conference_template, create_club_layout,
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
    def __init__(self, item_id, x, y, item_type, w=30, h=30, parent_id=None, rotation=0, label=""):
        self.id = item_id
        self.x = x
        self.y = y
        self.type = item_type
        self.w = w
        self.h = h
        self.parent_id = parent_id
        self.rotation = rotation
        self.label = label

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
    def __init__(self, data: MapItem, is_reserved=False):
        super().__init__(data)
        self.is_reserved = is_reserved
        self.is_selected = False
        self.visual_rect = QGraphicsRectItem(0, 0, data.w, data.h, self)
        self.visual_rect.setPen(QPen(Qt.black))
        self.update_color()

        font = QFont()
        font.setPixelSize(10)
        if len(data.id) > 4:
            font.setPixelSize(8)

        self.text = QGraphicsTextItem(data.id, self)
        self.text.setFont(font)
        br = self.text.boundingRect()
        self.text.setPos((data.w - br.width()) / 2, (data.h - br.height()) / 2)

    def update_color(self):
        c = COLORS["reserved"] if self.is_reserved else (COLORS["selected"] if self.is_selected else COLORS["free"])
        self.visual_rect.setBrush(QBrush(QColor(c)))

    def mousePressEvent(self, event):
        if self.is_reserved:
            return
        if self.flags() & QGraphicsItem.ItemIsSelectable:
            self.is_selected = not self.is_selected
            self.update_color()
        super().mousePressEvent(event)


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

        if self.mode == "add_seat":
            next_id = get_next_id("S", current_model)
            new_items.append({"id": next_id, "type": "seat", "x": tl_x, "y": tl_y, "w": 30, "h": 30, "rotation": 0})
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

        new_items = apply_rotation_to_group(new_items, cx, cy, self.current_rotation)
        for d in new_items:
            mi = MapItem(d["id"], d["x"], d["y"], d["type"], d.get("w", 30), d.get("h", 30),
                         d.get("parent_id"), d.get("rotation", 0), d.get("label", ""))
            self.parent().add_item(mi)
        super().mousePressEvent(event)


class SeatMapView(QGraphicsView):
    def __init__(self, layout_data=None, reserved_seats=None, parent=None, editable=False):
        super().__init__(parent)
        self.scene = InteractiveMapScene(self)
        self.setScene(self.scene)

        self.scene.setSceneRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setMouseTracking(True)
        self.editable = editable
        self.model = []
        self.setFocusPolicy(Qt.StrongFocus)

        raw_res = reserved_seats or set()
        self._reserved_seats = {str(s).strip().upper() for s in raw_res}
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
            mi = MapItem(d["id"], d["x"], d["y"], d["type"], d.get("w", 30), d.get("h", 30),
                         d.get("parent_id"), d.get("rotation", 0), d.get("label", ""))
            self.model.append(mi)
            self._draw(mi)

    def _draw(self, item: MapItem):
        gfx = None
        if item.type == "seat":
            cid = str(item.id).strip().upper()
            res = cid in self._reserved_seats
            gfx = GraphicSeat(item, res)
            if not self.editable and not res:
                gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
        else:
            gfx = GraphicShape(item)
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
        return [x.to_dict() for x in self.model]

    def get_selected_seats(self):
        return [i.data.id for i in self.scene.items() if isinstance(i, GraphicSeat) and i.is_selected]

    def set_mode(self, mode, config=None):
        self.scene.set_tool(mode, config)


class HallEditorWidget(QWidget):
    def __init__(self, current_layout=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.addWidget(QLabel("<b>Comenzi:</b><br>R - Rotire<br>Click - Plasare"))

        self.toolbox = QToolBox()

        # BAZA
        page_basic = QWidget()
        l_basic = QVBoxLayout(page_basic)
        self.rb_view = QRadioButton("Selectie / Muta")
        self.rb_del = QRadioButton("Sterge Element")
        self.rb_seat = QRadioButton("Scaun Simplu (S1...)")
        l_basic.addWidget(self.rb_view)
        l_basic.addWidget(self.rb_del)
        l_basic.addWidget(self.rb_seat)
        l_basic.addStretch()
        self.toolbox.addItem(page_basic, "Unelte De Baza")

        # MESE
        page_tables = QWidget()
        l_tables = QVBoxLayout(page_tables)

        self.rb_tr2 = QRadioButton("Masa Rotunda (2 pers)")
        self.rb_tr2.setProperty("tool_cfg", {"mode": "add_table_round", "seats": 2})

        self.rb_tr4 = QRadioButton("Masa Rotunda (4 pers)")
        self.rb_tr4.setProperty("tool_cfg", {"mode": "add_table_round", "seats": 4})

        self.rb_tr6 = QRadioButton("Masa Rotunda (6 pers)")
        self.rb_tr6.setProperty("tool_cfg", {"mode": "add_table_round", "seats": 6})

        self.rb_tr8 = QRadioButton("Masa Rotunda (8 pers)")
        self.rb_tr8.setProperty("tool_cfg", {"mode": "add_table_round", "seats": 8})

        self.rb_tr10 = QRadioButton("Masa Rotunda (10 pers)")
        self.rb_tr10.setProperty("tool_cfg", {"mode": "add_table_round", "seats": 10})

        self.rb_sq2 = QRadioButton("Masa Patrata (2 pers)")
        self.rb_sq2.setProperty("tool_cfg", {"mode": "add_table_rect", "seats": 2, "is_square": True})

        self.rb_sq4 = QRadioButton("Masa Patrata (4 pers)")
        self.rb_sq4.setProperty("tool_cfg", {"mode": "add_table_rect", "seats": 4, "is_square": True})

        self.rb_rec6 = QRadioButton("Masa Drept. (6 pers)")
        self.rb_rec6.setProperty("tool_cfg", {"mode": "add_table_rect", "seats": 6})

        self.rb_rec8 = QRadioButton("Masa Drept. (8 pers)")
        self.rb_rec8.setProperty("tool_cfg", {"mode": "add_table_rect", "seats": 8})

        l_tables.addWidget(self.rb_tr2)
        l_tables.addWidget(self.rb_tr4)
        l_tables.addWidget(self.rb_tr6)
        l_tables.addWidget(self.rb_tr8)
        l_tables.addWidget(self.rb_tr10)
        l_tables.addWidget(self.rb_sq2)
        l_tables.addWidget(self.rb_sq4)
        l_tables.addWidget(self.rb_rec6)
        l_tables.addWidget(self.rb_rec8)
        l_tables.addStretch()
        self.toolbox.addItem(page_tables, "Mese & Nunti")

        # DECOR
        page_decor = QWidget()
        l_decor = QVBoxLayout(page_decor)

        self.rb_scr = QRadioButton("Ecran Proiectie")
        self.rb_scr.setProperty("tool_cfg",
                                {"mode": "add_decor", "decor_type": "decor_screen", "label": "SCREEN", "w": 200,
                                 "h": 20})

        self.rb_stg = QRadioButton("Scena (Mica)")
        self.rb_stg.setProperty("tool_cfg",
                                {"mode": "add_decor", "decor_type": "decor_stage", "label": "SCENA", "w": 200,
                                 "h": 100})

        self.rb_stg_lg = QRadioButton("Scena (Mare)")
        self.rb_stg_lg.setProperty("tool_cfg",
                                   {"mode": "add_decor", "decor_type": "decor_stage", "label": "SCENA", "w": 400,
                                    "h": 150})

        self.rb_bar = QRadioButton("Bar")
        self.rb_bar.setProperty("tool_cfg",
                                {"mode": "add_decor", "decor_type": "decor_bar", "label": "BAR", "w": 150, "h": 60})

        self.rb_danc = QRadioButton("Ring Dans")
        self.rb_danc.setProperty("tool_cfg",
                                 {"mode": "add_decor", "decor_type": "decor_generic", "label": "DANCE", "w": 200,
                                  "h": 200})

        self.rb_ent = QRadioButton("Intrare")
        self.rb_ent.setProperty("tool_cfg",
                                {"mode": "add_decor", "decor_type": "decor_generic", "label": "INTRARE", "w": 100,
                                 "h": 40})

        l_decor.addWidget(self.rb_scr)
        l_decor.addWidget(self.rb_stg)
        l_decor.addWidget(self.rb_stg_lg)
        l_decor.addWidget(self.rb_bar)
        l_decor.addWidget(self.rb_danc)
        l_decor.addWidget(self.rb_ent)
        l_decor.addStretch()
        self.toolbox.addItem(page_decor, "Decor & Facilitati")

        sb_layout.addWidget(self.toolbox)

        self.btn_tmpl = QPushButton("Aplica Sablon...")
        self.btn_tmpl.clicked.connect(self.on_template)
        sb_layout.addWidget(self.btn_tmpl)

        self.btn_clear = QPushButton("Goleste Tot")
        self.btn_clear.setStyleSheet("background-color: #ffcdd2; color: #b71c1c;")
        self.btn_clear.clicked.connect(self.on_clear)
        sb_layout.addWidget(self.btn_clear)

        sidebar.layout().addStretch()
        layout.addWidget(sidebar)

        self.bg = QButtonGroup(self)
        all_rbs = [self.rb_view, self.rb_del, self.rb_seat, self.rb_tr2, self.rb_tr4, self.rb_tr6, self.rb_tr8,
                   self.rb_tr10, self.rb_sq2, self.rb_sq4, self.rb_rec6, self.rb_rec8, self.rb_scr, self.rb_stg,
                   self.rb_stg_lg, self.rb_bar, self.rb_danc, self.rb_ent]

        for rb in all_rbs:
            self.bg.addButton(rb)

        self.bg.buttonClicked.connect(self.on_tool_change)
        self.rb_view.setChecked(True)
        self.map_view = SeatMapView(current_layout, parent=self, editable=True)
        layout.addWidget(self.map_view)

    def on_tool_change(self, btn):
        cfg = btn.property("tool_cfg")
        if btn == self.rb_view:
            self.map_view.set_mode("view")
        elif btn == self.rb_del:
            self.map_view.set_mode("delete")
        elif btn == self.rb_seat:
            self.map_view.set_mode("add_seat")
        elif cfg:
            self.map_view.set_mode(cfg["mode"], cfg)

    def on_clear(self):
        if QMessageBox.question(self, "Atentie", "Sigur stergeti tot?") == QMessageBox.Yes:
            self.map_view.load_data([])

    def on_template(self):
        opts = ("Cinema Mic (5x8)", "Cinema Mare (10x12)", "Sala Conferinta", "Sala Nunta (Mica)", "Sala Nunta (Mare)",
                "Club / Lounge")
        sel, ok = QInputDialog.getItem(self, "Sablon", "Alege:", opts, 0, False)
        if ok and sel:
            items = []
            if "Cinema Mic" in sel:
                items = create_cinema_template(rows=5, cols_per_side=4)
            elif "Cinema Mare" in sel:
                items = create_cinema_template(rows=10, cols_per_side=6)
            elif "Sala Conferinta" in sel:
                items = create_conference_template()
            elif "Sala Nunta (Mica)" in sel:
                items = create_wedding_template("small")
            elif "Sala Nunta (Mare)" in sel:
                items = create_wedding_template("large")
            elif "Club" in sel:
                items = create_club_layout()

            if QMessageBox.question(self, "Confirm", "Inlocuiesti harta curenta?") == QMessageBox.Yes:
                self.map_view.load_data(items)

    def get_data(self):
        return self.map_view.get_layout_data()


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

        l_data = hall.get("layout", [])
        if isinstance(l_data, dict):
            l_data = []

        self.mv = SeatMapView(l_data, reserved_seats=res, parent=self, editable=False)
        layout.addWidget(self.mv)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_selected_seats(self):
        return self.mv.get_selected_seats()