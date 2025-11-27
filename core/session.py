from typing import Optional, Tuple

_current_email: Optional[str] = None
_current_role: Optional[str] = None


def set_current_user(email: str, role: str) -> None:
    global _current_email, _current_role
    _current_email = (email or "").strip()
    _current_role = role


def clear_current_user() -> None:
    global _current_email, _current_role
    _current_email = None
    _current_role = None


def get_current_user() -> Tuple[Optional[str], Optional[str]]:
    return _current_email, _current_role
