from typing import List, Dict, Optional
from core.db import get_connection


def list_events() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT e.id, e.title, e.description, e.date, e.time,
               h.id AS hall_id, h.name AS hall_name
        FROM events e
        JOIN halls h ON e.hall_id = h.id
        ORDER BY e.date, e.time, e.title;
        """
    )

    rows = cur.fetchall()
    conn.close()

    events = []
    for row in rows:
        event_id, title, description, date, time, hall_id, hall_name = row
        events.append(
            {
                "id": event_id,
                "title": title,
                "description": description or "",
                "date": date,
                "time": time,
                "hall_id": hall_id,
                "hall_name": hall_name,
            }
        )

    return events


def get_event(event_id: int) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT e.id, e.title, e.description, e.date, e.time,
               e.hall_id, h.name AS hall_name
        FROM events e
        JOIN halls h ON e.hall_id = h.id
        WHERE e.id = ?;
        """,
        (event_id,),
    )

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    event_id, title, description, date, time, hall_id, hall_name = row
    return {
        "id": event_id,
        "title": title,
        "description": description or "",
        "date": date,
        "time": time,
        "hall_id": hall_id,
        "hall_name": hall_name,
    }


def create_event(
    title: str,
    description: str,
    date: str,
    time: str,
    hall_id: int,
) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO events (title, description, date, time, hall_id)
        VALUES (?, ?, ?, ?, ?);
        """,
        (title, description, date, time, hall_id),
    )

    conn.commit()
    conn.close()


def update_event(
    event_id: int,
    title: str,
    description: str,
    date: str,
    time: str,
    hall_id: int,
) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE events
        SET title = ?, description = ?, date = ?, time = ?, hall_id = ?
        WHERE id = ?;
        """,
        (title, description, date, time, hall_id, event_id),
    )

    conn.commit()
    conn.close()


def delete_event(event_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM events WHERE id = ?;", (event_id,))
    conn.commit()
    conn.close()