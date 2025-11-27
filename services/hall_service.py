import json
from typing import List, Dict
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
    """Returnează toate sălile ca liste de dict-uri."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, layout_json FROM halls ORDER BY name;")
    rows = cur.fetchall()
    conn.close()

    halls = []
    for hall_id, name, layout_json in rows:
        halls.append(
            {
                "id": hall_id,
                "name": name,
                "layout_json": layout_json,  # string, putem parsa când avem nevoie
            }
        )

    return halls
