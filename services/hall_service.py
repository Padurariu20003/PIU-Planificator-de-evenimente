import json
from typing import List, Dict, Optional, Any
from core.db import get_connection

LOGICAL_WIDTH = 1600
LOGICAL_HEIGHT = 900


def _default_zones() -> List[Dict]:
    return [
        {"id": "Z1", "name": "Standard", "price": 50.0, "color": "#BBDEFB"},
        {"id": "Z2", "name": "VIP", "price": 100.0, "color": "#FFE0B2"},
    ]

def _dedup_zones(zones: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for z in zones:
        zid = str(z.get("id") or "").strip()
        if not zid or zid in seen:
            continue
        seen.add(zid)
        name = str(z.get("name") or zid).strip()
        try:
            price = float(z.get("price", 0))
        except Exception:
            price = 0.0
        color = str(z.get("color") or "").strip()
        d = {"id": zid, "name": name, "price": price}
        if color:
            d["color"] = color
        out.append(d)
    if "Z1" not in seen:
        out = [{"id": "Z1", "name": "Standard", "price": 50.0, "color": "#BBDEFB"}] + out
    return out


def _center_items(items: List[Dict], scene_w: int = LOGICAL_WIDTH, scene_h: int = LOGICAL_HEIGHT) -> List[Dict]:
    if not items:
        return items

    def gx(i, k, d=0.0):
        try:
            return float(i.get(k, d))
        except Exception:
            return d

    min_x = min(gx(i, "x") for i in items)
    max_x = max(gx(i, "x") + gx(i, "w", 30.0) for i in items)
    min_y = min(gx(i, "y") for i in items)
    max_y = max(gx(i, "y") + gx(i, "h", 30.0) for i in items)

    group_w = max_x - min_x
    group_h = max_y - min_y

    off_x = (scene_w - group_w) / 2 - min_x
    off_y = (scene_h - group_h) / 2 - min_y

    for i in items:
        i["x"] = gx(i, "x") + off_x
        i["y"] = gx(i, "y") + off_y

    return items


def _grid_to_items(rows: int, cols: int, zone_id: str = "Z1") -> List[Dict]:
    seat_size = 30
    gap = 5
    items: List[Dict] = []
    for r in range(rows):
        row_char = chr(ord("A") + r)
        for c in range(cols):
            items.append(
                {
                    "id": f"{row_char}{c + 1}",
                    "type": "seat",
                    "x": c * (seat_size + gap),
                    "y": r * (seat_size + gap),
                    "w": seat_size,
                    "h": seat_size,
                    "rotation": 0,
                    "zone_id": zone_id,
                }
            )
    return _center_items(items)


def _normalize_items(items: Any) -> List[Dict]:
    if not isinstance(items, list):
        return []
    out: List[Dict] = []
    for d in items:
        if not isinstance(d, dict):
            continue
        if "id" not in d or "type" not in d:
            continue
        nd = dict(d)
        t = str(nd.get("type") or "").strip()
        if t == "seat":
            zid = str(nd.get("zone_id") or "Z1").strip() or "Z1"
            nd["zone_id"] = zid
        out.append(nd)
    return out


def _parse_layout_json(layout_json: str) -> Dict[str, Any]:
    try:
        data = json.loads(layout_json) if layout_json else None
    except Exception:
        data = None

    zones = _default_zones()
    items: List[Dict] = []

    if isinstance(data, dict):
        if "items" in data:
            items = data.get("items") or []
            zones = data.get("zones") or zones
        elif "rows" in data and "cols" in data:
            try:
                rows = int(data.get("rows", 0))
                cols = int(data.get("cols", 0))
            except Exception:
                rows, cols = 0, 0
            if rows > 0 and cols > 0:
                items = _grid_to_items(rows, cols, "Z1")
    elif isinstance(data, list):
        items = data

    zones = _dedup_zones(zones if isinstance(zones, list) else _default_zones())
    items = _normalize_items(items)
    for it in items:
        if it.get("type") == "seat" and not str(it.get("zone_id") or "").strip():
            it["zone_id"] = "Z1"

    return {"items": items, "zones": zones}



def init_default_halls() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM halls;")
    count = cur.fetchone()[0]

    if count == 0:
        halls = [
            {"name": "Sala Mare", "rows": 10, "cols": 12},
            {"name": "Sala Mică", "rows": 5, "cols": 8},
            {"name": "Amfiteatru", "rows": 8, "cols": 15},
        ]

        zones = _default_zones()
        for h in halls:
            items = _grid_to_items(int(h["rows"]), int(h["cols"]), "Z1")
            payload = {"items": items, "zones": zones}
            cur.execute(
                "INSERT INTO halls (name, layout_json) VALUES (?, ?);",
                (h["name"], json.dumps(payload)),
            )
        conn.commit()

    conn.close()


def get_all_halls() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, layout_json FROM halls ORDER BY name;")
    rows = cur.fetchall()
    conn.close()

    halls: List[Dict] = []
    for hall_id, name, layout_json in rows:
        parsed = _parse_layout_json(layout_json)
        halls.append(
            {
                "id": hall_id,
                "name": name,
                "layout": parsed["items"],
                "zones": parsed["zones"],
                "layout_json": layout_json,
            }
        )

    return halls


def get_hall(hall_id: int) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, layout_json FROM halls WHERE id = ?;",
        (hall_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    hid, name, layout_json = row
    parsed = _parse_layout_json(layout_json)

    return {
        "id": hid,
        "name": name,
        "layout": parsed["items"],
        "zones": parsed["zones"],
        "layout_json": layout_json,
    }


def create_hall(name: str, layout_or_rows, cols: Optional[int] = None, zones: Optional[List[Dict]] = None) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")

    if cols is None and isinstance(layout_or_rows, (list, dict)):
        layout_data = layout_or_rows
        if isinstance(layout_data, dict) and "items" in layout_data:
            items = _normalize_items(layout_data.get("items") or [])
            z = _dedup_zones(layout_data.get("zones") or _default_zones())
        else:
            items = _normalize_items(layout_data if isinstance(layout_data, list) else [])
            z = _dedup_zones(zones or _default_zones())
    else:
        try:
            rows = int(layout_or_rows)
        except Exception:
            raise ValueError("Numarul de randuri trebuie sa fie un numar intreg pozitiv.")
        if cols is None:
            raise ValueError("Numarul de coloane este obligatoriu.")
        try:
            cols_int = int(cols)
        except Exception:
            raise ValueError("Numarul de coloane trebuie sa fie un numar intreg pozitiv.")
        if rows <= 0 or cols_int <= 0:
            raise ValueError("Numarul de randuri si coloane trebuie sa fie pozitiv.")
        items = _grid_to_items(rows, cols_int, "Z1")
        z = _dedup_zones(zones or _default_zones())

    payload = {"items": items, "zones": z}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO halls (name, layout_json) VALUES (?, ?);",
        (name, json.dumps(payload)),
    )
    conn.commit()
    conn.close()


def update_hall(hall_id: int, name: str, layout_items: List[Dict], zones: Optional[List[Dict]] = None) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")

    items = _normalize_items(layout_items)
    z = _dedup_zones(zones or _default_zones())

    payload = {"items": items, "zones": z}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE halls
        SET name = ?, layout_json = ?
        WHERE id = ?;
        """,
        (name, json.dumps(payload), hall_id),
    )
    conn.commit()
    conn.close()

def delete_hall(hall_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM halls WHERE id = ?;", (hall_id,))
    conn.commit()
    conn.close()