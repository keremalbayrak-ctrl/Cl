"""Per-client living record of what is exposed, where, and remediation status."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExposureItem:
    client_id: str
    source: str
    description: str
    detected_at: str = field(default_factory=_now)
    status: str = "open"  # open | reducing | resolved | monitoring
    evidence: dict = field(default_factory=dict)


class ExposureRegister:
    def __init__(self):
        self._items: dict = {}

    def add(self, item: ExposureItem) -> None:
        self._items.setdefault(item.client_id, []).append(item)

    def for_client(self, client_id: str) -> list:
        return self._items.get(client_id, [])

    def update_status(self, client_id: str, index: int, status: str) -> None:
        self._items[client_id][index].status = status
