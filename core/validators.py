# core/validators.py
import re
from datetime import datetime

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Emailul este obligatoriu.")
    if not _EMAIL_RE.match(email):
        raise ValueError("Introduceti un email valid (ex: nume@domeniu.ro).")
    return email


def validate_date(date_str: str) -> str:
    date_str = (date_str or "").strip()
    if not date_str:
        raise ValueError("Data este obligatorie.")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(
            "Data trebuie sa fie in formatul YYYY-MM-DD (ex: 2025-12-31)."
        )
    return date_str


def validate_time(time_str: str) -> str:
    time_str = (time_str or "").strip()
    if not time_str:
        raise ValueError("Ora este obligatorie.")
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        raise ValueError(
            "Ora trebuie sa fie in formatul HH:MM (ex: 09:30 sau 18:45)."
        )
    return time_str
