import json
from typing import List, Dict, Optional
from core.db import get_connection


def init_default_halls() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM halls;")
    count = cur.fetchone()[0]

    if count == 0:
        halls = [
            {
                "name": "Sala Mare",
                "layout": {"rows": 10, "cols": 12},
            },
            {
                "name": "Sala Mică",
                "layout": {"rows": 5, "cols": 8},
            },
            {
                "name": "Amfiteatru",
                "layout": {"rows": 8, "cols": 15},
            },
        ]

        for hall in halls:
            cur.execute(
                "INSERT INTO halls (name, layout_json) VALUES (?, ?);",
                (hall["name"], json.dumps(hall["layout"])),
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
        try:
            layout = json.loads(layout_json)
        except json.JSONDecodeError:
            layout = {}

        halls.append(
            {
                "id": hall_id,
                "name": name,
                "layout": layout,
                "layout_json": layout_json
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
    try:
        layout = json.loads(layout_json)
    except json.JSONDecodeError:
        layout = {}

    return {
        "id": hid,
        "name": name,
        "layout": layout,
        "layout_json": layout_json,
    }


def create_hall(name: str, layout_or_rows, cols: Optional[int] = None) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")
    
    if cols is None and isinstance(layout_or_rows, (list, dict)):
        layout = layout_or_rows
        if not layout:
            raise ValueError("Configuratia salii nu poate fi goala.")
    else:
        try:
            rows = int(layout_or_rows)
        except (TypeError, ValueError):
            raise ValueError("Numarul de randuri trebuie sa fie un numar intreg pozitiv.")

        if cols is None:
            raise ValueError("Numarul de coloane este obligatoriu.")
        try:
            cols_int = int(cols)
        except (TypeError, ValueError):
            raise ValueError("Numarul de coloane trebuie sa fie un numar intreg pozitiv.")

        if rows <= 0 or cols_int <= 0:
            raise ValueError("Numarul de randuri si coloane trebuie sa fie pozitiv.")

        layout = {"rows": rows, "cols": cols_int}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO halls (name, layout_json) VALUES (?, ?);",
        (name, json.dumps(layout)),
    )
    conn.commit()
    conn.close()



def update_hall(hall_id: int, name: str, layout_data: List) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE halls
        SET name = ?, layout_json = ?
        WHERE id = ?;
        """,
        (name, json.dumps(layout_data), hall_id),
    )
    conn.commit()
    conn.close()
def delete_hall(hall_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM halls WHERE id = ?;", (hall_id,))
    conn.commit()
    conn.close()
