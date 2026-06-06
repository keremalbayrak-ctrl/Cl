"""Sanctions / PEP screening of the CLIENT'S OWN identity.

Screens the client (person) or a client-declared entity against an allowlisted
sanctions or PEP list, to show the client their own status (methodology strategy
14). The subject must be in consent scope, enforced by the base class; this never
screens a third party. Instantiate one per list (each `source_id` allowlisted).
"""
from __future__ import annotations

from ..guardrails import Subject
from .base import Collector


class SanctionsScreeningCollector(Collector):
    def __init__(self, allowlist, consent, source_id, screening_client):
        super().__init__(allowlist, consent)
        self.source_id = source_id
        self.screen = screening_client

    def _fetch(self, subject: Subject) -> list:
        if subject.kind not in ("person", "entity"):
            return []
        matches = self.screen.screen(subject.identifier, self.source_id)
        return [{
            "source": self.source_id,
            "subject": subject.identifier,
            "kind": subject.kind,
            "matches": matches,
        }]
