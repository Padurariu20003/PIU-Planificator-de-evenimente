import json
from datetime import datetime
from typing import List, Dict
from core.db import get_connection
from services import event_service, hall_service

def _normalize_seats(seats: List[str]) -> List[str]:
    result = []
    for s in seats:
        if s is None:
            continue
        seat = str(s).strip()
        if seat == "":
            continue
        result.append(seat.upper())
    return result

def preview_total(event_id: int, seats: List[str]) -> float:
    seats_n = _normalize_seats(seats)
    if not seats_n:
        return 0.0

    ev = event_service.get_event(event_id)
    if not ev:
        return 0.0

    hall = hall_service.get_hall(ev["hall_id"])
    if not hall:
        return 0.0

    zones = hall.get("zones", [])
    zprice = {}
    for z in zones:
        zid = str(z.get("id") or "").strip()
        try:
            price = float(z.get("price", 0))
        except Exception:
            price = 0.0
        if zid:
            zprice[zid] = price

    seat_zone = {}
    for it in hall.get("layout", []):
        if it.get("type") == "seat":
            sid = str(it.get("id") or "").strip().upper()
            zid = str(it.get("zone_id") or "Z1").strip() or "Z1"
            if sid:
                seat_zone[sid] = zid

    total = 0.0
    for s in seats_n:
        zid = seat_zone.get(s, "Z1")
        total += float(zprice.get(zid, 0.0))

    return float(total)



def list_bookings_for_event(event_id: int) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, seats_json, created_at, total_price
        FROM bookings
        WHERE event_id = ?
        ORDER BY created_at;
        """,
        (event_id,),
    )

    rows = cur.fetchall()
    conn.close()

    bookings: List[Dict] = []
    for booking_id, name, email, seats_json, created_at, total_price in rows:
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
                "total_price": float(total_price or 0),
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
            b.total_price,
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
        total_price,
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
                "total_price": float(total_price or 0),
                "event_title": event_title,
                "event_date": event_date,
                "event_time": event_time,
                "hall_name": hall_name,
            }
        )

    return bookings


def create_booking(event_id: int, name: str, email: str, seats: List[str]) -> None:
    normalized_seats = _normalize_seats(seats)
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
            seat = str(s).strip().upper()
            if seat:
                reserved_seats.add(seat)

    conflict = reserved_seats.intersection(normalized_seats)
    if conflict:
        conn.close()
        raise ValueError(
            f"Urmatoarele locuri sunt deja rezervate: {', '.join(sorted(conflict))}"
        )

    created_at = datetime.now().isoformat(timespec="seconds")
    total = preview_total(event_id, normalized_seats)

    cur.execute(
        """
        INSERT INTO bookings (event_id, name, email, seats_json, created_at, total_price)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (event_id, name, email, json.dumps(normalized_seats), created_at, float(total)),
    )

    conn.commit()
    conn.close()
