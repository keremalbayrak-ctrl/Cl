"""Builds collectors for allowlisted sources from injected adapters.

`adapters` maps source_id -> adapter. A source gets an automated collector only
if it is (a) on the allowlist and (b) permits automation. Everything else is
reported — sources whose terms do not permit automation as `manual_only` (a
human must integrate them under their terms), and unknown ids as `skipped`. This
turns "cover all these countries" into configuration over one tested collector.
"""
from __future__ import annotations

from .collectors.register import RegisterCollector


class CollectorRegistry:
    def __init__(self, allowlist, consent, adapters, subject_kinds=None):
        self.allowlist = allowlist
        self.consent = consent
        self.adapters = dict(adapters)
        self.subject_kinds = dict(subject_kinds or {})

    def build(self) -> dict:
        collectors, manual_only, skipped = {}, [], []
        for source_id, adapter in self.adapters.items():
            if not self.allowlist.contains(source_id):
                skipped.append(source_id)
                continue
            if not self.allowlist.get(source_id).terms_permit_automation:
                manual_only.append(source_id)
                continue
            kind = self.subject_kinds.get(source_id, "entity")
            collectors[source_id] = RegisterCollector(
                self.allowlist, self.consent, source_id, adapter, kind)
        return {
            "collectors": collectors,
            "manual_only": sorted(manual_only),
            "skipped": sorted(skipped),
        }
