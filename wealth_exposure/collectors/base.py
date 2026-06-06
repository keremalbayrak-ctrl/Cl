"""Base collector.

Every collection passes through the guardrails before any network call: the
source must be allowlisted, the subject must be in consent scope, and the
source's automation terms and rate limit are respected. A `_fetch` that returns
nothing is recorded as an absence, not an inferred presence.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod

from ..guardrails import (
    Subject,
    assert_in_consent_scope,
    assert_source_allowed,
    record_absence_not_presence,
)


class Collector(ABC):
    source_id: str

    def __init__(self, allowlist, consent):
        self.allowlist = allowlist
        self.consent = consent
        self._last_call = 0.0

    def _respect_rate_limit(self) -> None:
        src = self.allowlist.get(self.source_id)
        if not src.terms_permit_automation:
            raise PermissionError(
                f"{self.source_id}: terms do not permit automation."
            )
        min_gap = 60.0 / max(src.rate_limit_per_min, 1)
        gap = time.monotonic() - self._last_call
        if gap < min_gap:
            time.sleep(min_gap - gap)
        self._last_call = time.monotonic()

    def collect(self, subject: Subject) -> list:
        assert_source_allowed(self.source_id, self.allowlist)
        assert_in_consent_scope(subject, self.consent)
        self._respect_rate_limit()
        return record_absence_not_presence(self._fetch(subject))

    @abstractmethod
    def _fetch(self, subject: Subject) -> list:
        raise NotImplementedError
