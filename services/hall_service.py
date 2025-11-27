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


def create_hall(name: str, rows: int, cols: int) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")
    if rows <= 0 or cols <= 0:
        raise ValueError("Numarul de randuri si coloane trebuie sa fie pozitiv.")

    layout = {"rows": rows, "cols": cols}

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO halls (name, layout_json) VALUES (?, ?);",
        (name, json.dumps(layout)),
    )

    conn.commit()
    conn.close()


def update_hall(hall_id: int, name: str, rows: int, cols: int) -> None:
    name = (name or "").strip()
    if not name:
        raise ValueError("Numele salii este obligatoriu.")
    if rows <= 0 or cols <= 0:
        raise ValueError("Numarul de randuri si coloane trebuie sa fie pozitiv.")

    layout = {"rows": rows, "cols": cols}

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE halls
        SET name = ?, layout_json = ?
        WHERE id = ?;
        """,
        (name, json.dumps(layout), hall_id),
    )

    conn.commit()
    conn.close()


def delete_hall(hall_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM halls WHERE id = ?;", (hall_id,))
    conn.commit()
    conn.close()
