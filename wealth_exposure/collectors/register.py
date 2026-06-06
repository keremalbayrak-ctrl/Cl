"""Generic collector for any allowlisted register/source.

This is how the system covers many jurisdictions without bespoke code per
register. It works against any source via an injected `adapter` that knows how
to call that source's official API under its terms of use. It accepts only
subjects of `subject_kind` (default "entity"), and the base class enforces
consent scope + allowlist + rate limit before any call — so a one-line
configuration entry adds a country, with the same guardrails.

Adapter contract: `adapter.fetch(identifier) -> list[dict] | None`.
"""
from __future__ import annotations

from ..guardrails import Subject
from .base import Collector


class RegisterCollector(Collector):
    def __init__(self, allowlist, consent, source_id, adapter, subject_kind="entity"):
        super().__init__(allowlist, consent)
        self.source_id = source_id
        self.adapter = adapter
        self.subject_kind = subject_kind

    def _fetch(self, subject: Subject) -> list:
        if subject.kind != self.subject_kind:
            return []
        records = self.adapter.fetch(subject.identifier)
        if not records:
            return []
        return [{
            "source": self.source_id,
            "subject": subject.identifier,
            "records": records,
        }]
