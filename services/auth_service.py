import hashlib
import sqlite3
from typing import Optional

from core.db import get_connection


SALT = "eventease_salt_2025"


def hash_password(password: str) -> str:
    data = (SALT + password).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def init_default_admin() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", ("admin@eventease.local",))
    row = cur.fetchone()

    if row is None:
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?);",
            ("admin@eventease.local", hash_password("admin"), "admin"),
        )
        conn.commit()

    conn.close()


def create_user(email: str, password: str) -> None:
    email = (email or "").strip()
    password = password or ""

    if not email or not password:
        raise ValueError("Email si parola obligatorii.")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'user');",
            (email, hash_password(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Exista deja un cont cu acest email.")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def login(email: str, password: str) -> Optional[str]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT password_hash, role FROM users WHERE email = ?;",
        (email,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    stored_hash, role = row
    if stored_hash == hash_password(password):
        return role

    return None
