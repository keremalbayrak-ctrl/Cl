"""Full per-client exposure sweep.

`ExposureRun.run` is the single entry point that does the whole thing for ONE
client: it runs the configured collectors against every subject the client
declared as their own (entities, identifiers, the person), assesses declared
counterparties, correlates the results, and writes counterparty risk flags to
the exposure register.

Every query is seeded from `consent.subjects_for(client_id, ...)`, so the sweep
can only ever touch the given client's own declared data — there is no way to
sweep an arbitrary target.
"""
from __future__ import annotations

from .exposure_register import ExposureItem
from .guardrails import Subject


class ExposureRun:
    def __init__(self, consent, register, resolver=None):
        self.consent = consent
        self.register = register
        self.resolver = resolver

    def run(self, client_id, entity_collectors=None, identifier_collectors=None,
            person_collectors=None, counterparty_assessor=None) -> dict:
        records = []
        for entity in self.consent.subjects_for(client_id, "entity"):
            records += self._sweep(Subject(entity, "entity"), entity_collectors)
        for identifier in self.consent.subjects_for(client_id, "identifier"):
            records += self._sweep(Subject(identifier, "identifier"), identifier_collectors)
        for person in self.consent.subjects_for(client_id, "person"):
            records += self._sweep(Subject(person, "person"), person_collectors)

        counterparties = []
        if counterparty_assessor is not None:
            for firm in self.consent.subjects_for(client_id, "counterparty"):
                assessment = counterparty_assessor.assess(firm)
                counterparties.append(assessment)
                for flag in assessment["risk_flags"]:
                    self.register.add(ExposureItem(
                        client_id, "counterparty_dd",
                        f"Counterparty risk: {flag} ({firm})",
                        evidence={"assessment": assessment}))

        correlation = None
        if self.resolver is not None:
            correlation = self.resolver.correlate(
                [r for r in records if isinstance(r, dict) and "claims" in r])

        return {
            "client": client_id,
            "records": records,
            "counterparties": counterparties,
            "correlation": correlation,
        }

    @staticmethod
    def _sweep(subject, collectors) -> list:
        out = []
        for collector in (collectors or {}).values():
            out += collector.collect(subject)
        return out
