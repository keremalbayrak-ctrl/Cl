"""Own-data-only breach/exposure collector.

Accepts ONLY the client's declared identifiers, checked via a licensed exposure
provider. It never queries a raw leaked database and never accepts a third-party
identifier (`assert_own_identifier_only` enforces this, on top of the base
class's consent-scope check). This is the lawful version of "check leak
exposure".
"""
from __future__ import annotations

from ..guardrails import Subject, assert_own_identifier_only
from .base import Collector


class BreachExposureCollector(Collector):
    source_id = "breach_licensed_provider"

    def __init__(self, allowlist, consent, licensed_provider):
        super().__init__(allowlist, consent)
        self.provider = licensed_provider

    def _fetch(self, subject: Subject) -> list:
        if subject.kind != "identifier":
            return []
        assert_own_identifier_only(subject.identifier, self.consent)
        hits = self.provider.check_own_exposure(subject.identifier)
        return [{
            "source": self.source_id,
            "identifier": subject.identifier,
            "exposure": hits,
        }]
