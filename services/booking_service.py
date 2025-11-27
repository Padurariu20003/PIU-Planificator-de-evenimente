import json
from datetime import datetime
from typing import List, Dict
from core.db import get_connection


def list_bookings_for_event(event_id: int) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, seats_json, created_at
        FROM bookings
        WHERE event_id = ?
        ORDER BY created_at;
        """,
        (event_id,),
    )

    rows = cur.fetchall()
    conn.close()

    bookings: List[Dict] = []
    for booking_id, name, email, seats_json, created_at in rows:
        try:
            seats = json.loads(seats_json)
        except json.JSONDecodeError:
            seats = []

        bookings.append(
            {
                "id": booking_id,
                "name": name,
                "email": email,
                "seats": seats,
                "created_at": created_at,
            }
        )

    return bookings


def list_bookings_for_email(email: str) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            b.id,
            b.name,
            b.email,
            b.seats_json,
            b.created_at,
            e.title,
            e.date,
            e.time,
            h.name AS hall_name
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        JOIN halls h ON e.hall_id = h.id
        WHERE b.email = ?
        ORDER BY b.created_at DESC;
        """,
        (email,),
    )

    rows = cur.fetchall()
    conn.close()

    bookings: List[Dict] = []
    for (
        booking_id,
        name,
        email_val,
        seats_json,
        created_at,
        event_title,
        event_date,
        event_time,
        hall_name,
    ) in rows:
        try:
            seats = json.loads(seats_json)
        except json.JSONDecodeError:
            seats = []

        bookings.append(
            {
                "id": booking_id,
                "name": name,
                "email": email_val,
                "seats": seats,
                "created_at": created_at,
                "event_title": event_title,
                "event_date": event_date,
                "event_time": event_time,
                "hall_name": hall_name,
            }
        )

    return bookings


def create_booking(event_id: int, name: str, email: str, seats: List[str]) -> None:
    normalized_seats = [s.strip().upper() for s in seats if s.strip()]
    if not normalized_seats:
        raise ValueError("Trebuie sa selectati cel putin un loc.")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT seats_json FROM bookings WHERE event_id = ?;",
        (event_id,),
    )
    rows = cur.fetchall()

    reserved_seats = set()
    for (seats_json,) in rows:
        try:
            existing = json.loads(seats_json)
        except json.JSONDecodeError:
            existing = []
        for s in existing:
            reserved_seats.add(str(s).strip().upper())

    conflict = reserved_seats.intersection(normalized_seats)
    if conflict:
        conn.close()
        raise ValueError(
            f"Urmatoarele locuri sunt deja rezervate: {', '.join(sorted(conflict))}"
        )

    created_at = datetime.now().isoformat(timespec="seconds")

    cur.execute(
        """
        INSERT INTO bookings (event_id, name, email, seats_json, created_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        (event_id, name, email, json.dumps(normalized_seats), created_at),
    )

    conn.commit()
    conn.close()
