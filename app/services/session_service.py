from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CustomerSession:
    phone: str
    history: list[dict] = field(default_factory=list)
    confirmed_orders: list[dict] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_sessions: dict[str, CustomerSession] = {}


def get_session(phone: str) -> CustomerSession:
    if phone not in _sessions:
        _sessions[phone] = CustomerSession(phone=phone)
    session = _sessions[phone]
    session.updated_at = datetime.now(timezone.utc)
    return session


def reset_session(phone: str) -> None:
    _sessions.pop(phone, None)


def save_confirmed_order(phone: str, order: dict) -> None:
    session = get_session(phone)
    session.confirmed_orders.append(order)
