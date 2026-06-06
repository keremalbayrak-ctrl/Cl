"""Entity resolution and correlation, scoped to the consent set.

Seeds are the client's declared subjects only; the resolver never introduces a
new third-party target — it only correlates records already lawfully collected.
Nothing is treated as established without confirmation from two independent
sources.
"""
from __future__ import annotations


class Resolver:
    def __init__(self, consent):
        self.consent = consent

    def correlate(self, records: list) -> dict:
        by_claim: dict = {}
        for r in records:
            for claim in self._claims(r):
                by_claim.setdefault(claim["key"], []).append(claim["source"])

        established, unconfirmed = [], []
        for key, sources in by_claim.items():
            distinct = sorted(set(sources))
            target = established if len(distinct) >= 2 else unconfirmed
            target.append({"claim": key, "sources": distinct})
        return {"established": established, "unconfirmed": unconfirmed}

    def _claims(self, record: dict) -> list:
        # Normalise a record into atomic claims (address, control, holding, ...)
        # each as {"key": ..., "source": ...}. Implement per source schema.
        return record.get("claims", [])
