"""Concrete foresight watchers (early detection).

Each wraps an injected public-feed client and maps changes to consent-scoped
subjects only. The injected client is responsible for reading the underlying
allowlisted source under its terms of use; these classes enforce that only
in-scope subjects are ever flagged.
"""
from __future__ import annotations

from ..guardrails import Subject
from .base import Watcher


class RegisterChangeWatcher(Watcher):
    """New filings / PSC changes / charge registrations on the client's own
    declared entities (e.g. a Companies House follow/stream feed)."""

    feed_id = "register_change"

    def __init__(self, allowlist, consent, feed_client):
        super().__init__(allowlist, consent)
        self.feed = feed_client

    def detect_changes(self) -> list:
        return self.feed.poll() or []

    def map_to_subjects(self, change: dict) -> list:
        entity = change.get("entity")
        if not entity:
            return []
        subject = Subject(entity, "entity")
        return [subject] if self.consent.covers(subject) else []


class CounterpartyFilingWatcher(Watcher):
    """New filing / audit opinion / enforcement on a declared counterparty firm."""

    feed_id = "counterparty_filing"

    def __init__(self, allowlist, consent, feed_client):
        super().__init__(allowlist, consent)
        self.feed = feed_client

    def detect_changes(self) -> list:
        return self.feed.poll() or []

    def map_to_subjects(self, change: dict) -> list:
        firm = change.get("firm")
        if not firm:
            return []
        subject = Subject(firm, "counterparty")
        return [subject] if self.consent.covers(subject) else []


class SanctionsUpdateWatcher(Watcher):
    """On a sanctions/PEP list update, re-screen the client's own watched
    subjects; flag only those (own) subjects that now match."""

    feed_id = "sanctions_update"

    def __init__(self, allowlist, consent, rescreen_client):
        super().__init__(allowlist, consent)
        self.rescreen = rescreen_client

    def detect_changes(self) -> list:
        return self.rescreen.updates() or []

    def map_to_subjects(self, change: dict) -> list:
        identifier = change.get("subject")
        kind = change.get("kind")
        if not identifier or kind not in ("person", "entity"):
            return []
        subject = Subject(identifier, kind)
        return [subject] if self.consent.covers(subject) else []
