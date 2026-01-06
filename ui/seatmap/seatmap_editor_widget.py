from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QMessageBox, QInputDialog,
    QToolBox, QComboBox, QColorDialog
)

from PySide6.QtGui import QIcon, QPixmap, QColor

from .seatmap_core import SeatMapView, GraphicSeat

from ..layout_generator import (
    create_cinema_template, create_wedding_template,
    create_conference_template, create_club_layout
)

class HallEditorWidget(QWidget):
    def __init__(self, current_layout=None, parent=None, zones=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.addWidget(QLabel("<b>Comenzi:</b><br>R - Rotire<br>Click - Plasare"))

        # ZONE (admin)
        self.zones = zones or [
            {"id": "Z1", "name": "VIP", "price": 100.0, "color": "#ED94FF"},
            {"id": "Z2", "name": "Standard", "price": 50.0, "color": "#92FCA7"},
        ]

        sb_layout.addWidget(QLabel("<b>Zone:</b>"))

        self.zone_combo = QComboBox()
        sb_layout.addWidget(self.zone_combo)

        self.btn_zone_add = QPushButton("Adauga zona")
        self.btn_zone_edit = QPushButton("Editeaza zona")
        self.btn_zone_del = QPushButton("Sterge zona")
        self.btn_apply_zone = QPushButton("Aplica zona la scaune selectate")

        sb_layout.addWidget(self.btn_zone_add)
        sb_layout.addWidget(self.btn_zone_edit)
        sb_layout.addWidget(self.btn_zone_del)
        sb_layout.addWidget(self.btn_apply_zone)

        self.btn_zone_add.clicked.connect(self.on_add_zone)
        self.btn_zone_edit.clicked.connect(self.on_edit_zone)
        self.btn_zone_del.clicked.connect(self.on_delete_zone)
        self.btn_apply_zone.clicked.connect(self.on_apply_zone)

        self.refresh_zone_combo()
        
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
        self.map_view = SeatMapView(current_layout, parent=self, editable=True, zones=self.zones)

        layout.addWidget(self.map_view)

    def on_tool_change(self, btn):
        cfg = btn.property("tool_cfg")
        zid = self.current_zone_id()

        if btn == self.rb_view:
            self.map_view.set_mode("view")
        elif btn == self.rb_del:
            self.map_view.set_mode("delete")
        elif btn == self.rb_seat:
            self.map_view.set_mode("add_seat", {"zone_id": zid})
        elif cfg:
            cfg2 = dict(cfg)
            cfg2["zone_id"] = zid
            self.map_view.set_mode(cfg2["mode"], cfg2)

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

    def refresh_zone_combo(self):
        self.zone_combo.clear()
        for z in self.zones:
            zid = str(z.get("id") or "").strip()
            name = str(z.get("name") or zid).strip()
            try:
                price = float(z.get("price", 0))
            except Exception:
                price = 0.0

            col = str(z.get("color") or "#BBDEFB").strip()

            if zid:
                pm = QPixmap(16, 16)
                pm.fill(QColor(col))
                icon = QIcon(pm)

                self.zone_combo.addItem(
                    icon,
                    f"{zid} - {name} ({price:.2f} lei)",
                    zid
                )

    def current_zone_id(self) -> str:
        zid = self.zone_combo.currentData()
        return str(zid or "Z1").strip() or "Z1"

    def _push_zones_to_map(self):
        # rebuild colors + meta in map view and redraw
        self.map_view._zones = self.zones

        self.map_view._zone_colors = {}
        for z in self.zones:
            zid = str(z.get("id") or "").strip()
            col = str(z.get("color") or "").strip()
            if zid and col:
                self.map_view._zone_colors[zid] = col

        self.map_view._zone_meta = {}
        for z in self.zones:
            zid = str(z.get("id") or "").strip()
            name = str(z.get("name") or zid).strip()
            try:
                price = float(z.get("price", 0))
            except Exception:
                price = 0.0
            if zid:
                self.map_view._zone_meta[zid] = (name, price)

        self.map_view.load_data(self.map_view.get_layout_data())

    def on_apply_zone(self):
        zid = self.current_zone_id()
        selected = self.map_view.scene.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Selectati scaunele (click / Ctrl+click).")
            return

        # aplica zona doar la scaune
        changed = 0
        for it in selected:
            seat = it if isinstance(it, GraphicSeat) else (it.parentItem() if it and isinstance(it.parentItem(), GraphicSeat) else None)
            if seat:
                seat.data.zone_id = zid
                changed += 1

        if changed == 0:
            QMessageBox.information(self, "Info", "Nu ati selectat scaune.")
            return

        self._push_zones_to_map()

    def on_add_zone(self):
        # id automat: Z{max+1}
        existing = []
        for z in self.zones:
            zid = str(z.get("id") or "").strip().upper()
            if zid.startswith("Z"):
                try:
                    existing.append(int(zid[1:]))
                except:
                    pass
        next_id = f"Z{(max(existing) + 1) if existing else 1}"

        name, ok = QInputDialog.getText(self, "Zona noua", f"Nume zona pentru {next_id} (ex: VIP / General):")
        if not ok:
            return
        name = (name or "").strip() or next_id

        price_str, ok = QInputDialog.getText(self, "Zona noua", f"Pret (lei) pentru {next_id}:")
        if not ok:
            return
        try:
            price = float(price_str.replace(",", "."))
        except:
            QMessageBox.warning(self, "Eroare", "Pret invalid.")
            return

        initial = QColor("#BBDEFB")
        picked = QColorDialog.getColor(initial, self, f"Culoare pentru {next_id}")
        if not picked.isValid():
            return
        color = picked.name()  

        self.zones.append({"id": next_id, "name": name, "price": price, "color": color})
        self.refresh_zone_combo()
        self._push_zones_to_map()

    def on_edit_zone(self):
        zid = self.current_zone_id()
        z = next((x for x in self.zones if str(x.get("id")).strip() == zid), None)
        if not z:
            return

        name, ok = QInputDialog.getText(self, "Editeaza zona", f"Nume pentru {zid}:", text=str(z.get("name") or zid))
        if not ok:
            return
        name = (name or "").strip() or zid

        price_str, ok = QInputDialog.getText(self, "Editeaza zona", f"Pret (lei) pentru {zid}:", text=str(z.get("price", 0)))
        if not ok:
            return
        try:
            price = float(price_str.replace(",", "."))
        except:
            QMessageBox.warning(self, "Eroare", "Pret invalid.")
            return

        initial = QColor(str(z.get("color") or "#BBDEFB"))
        picked = QColorDialog.getColor(initial, self, f"Culoare pentru {zid}")
        if not picked.isValid():
            return
        color = picked.name()

        z["name"] = name
        z["price"] = price
        z["color"] = color

        self.refresh_zone_combo()
        self._push_zones_to_map()

    def on_delete_zone(self):
        zid = self.current_zone_id()
        if zid == "Z1":
            QMessageBox.information(self, "Info", "Nu stergem Z1 (zona default).")
            return

        if QMessageBox.question(self, "Confirmare", f"Stergi zona {zid}? Scaunele din zona asta vor trece in Z1.") != QMessageBox.Yes:
            return

        # muta scaunele din zid -> Z1
        layout = self.map_view.get_layout_data()
        for it in layout:
            if it.get("type") == "seat" and it.get("zone_id") == zid:
                it["zone_id"] = "Z1"

        self.zones = [z for z in self.zones if str(z.get("id")).strip() != zid]
        self.refresh_zone_combo()

        self.map_view.load_data(layout)
        self._push_zones_to_map()

    def get_data(self):
        return {"items": self.map_view.get_layout_data(), "zones": self.zones}
