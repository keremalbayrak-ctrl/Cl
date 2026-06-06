"""Counterparty risk assessment for firms where the CLIENT holds assets.

Reads ONLY public, firm-level due-diligence data — regulatory status, filed
accounts including the audit opinion, enforcement actions, sanctions exposure —
about a firm the client has declared as a counterparty. This is lawful due
diligence on the client's own holdings ("is my money safe at firm X?"), anchored
to the client's own relationship. It is NOT third-party profiling, and NOT a
route to the firm's owners, customers, or anyone's wealth: the output is
firm-level risk only.

The firm must be a declared counterparty (consent gate) and every source it
reads must be allowlisted; both are enforced here. Early-warning flags surface
standing problems such as a qualified/adverse audit opinion or a going-concern
note before they become a loss.
"""
from __future__ import annotations

from .guardrails import (
    Subject,
    assert_in_consent_scope,
    assert_source_allowed,
    record_absence_not_presence,
)


class CounterpartyRiskAssessor:
    def __init__(self, allowlist, consent, dd_client, sources):
        self.allowlist = allowlist
        self.consent = consent
        self.dd = dd_client
        self.sources = list(sources)

    def assess(self, firm_id: str) -> dict:
        subject = Subject(firm_id, "counterparty")
        assert_in_consent_scope(subject, self.consent)  # declared counterparty only
        for source_id in self.sources:
            assert_source_allowed(source_id, self.allowlist)

        findings = {
            "regulatory_status": self.dd.regulatory_status(firm_id),
            "audit_opinion": self.dd.latest_audit_opinion(firm_id),
            "enforcement": record_absence_not_presence(
                self.dd.enforcement_actions(firm_id) or []),
            "sanctions": record_absence_not_presence(
                self.dd.sanctions_hits(firm_id) or []),
        }
        return {
            "firm": firm_id,
            "client": self.consent.owner_of(subject),
            "findings": findings,
            "risk_flags": self._flags(findings),
            "label": "counterparty risk from public sources; firm-level only",
        }

    @staticmethod
    def _flags(findings: dict) -> list:
        flags = []
        opinion_rec = findings.get("audit_opinion") or {}
        opinion = str(opinion_rec.get("opinion", "")).lower()
        if opinion in {"qualified", "adverse", "disclaimer"} or opinion_rec.get("going_concern"):
            flags.append("adverse_or_qualified_audit_opinion")

        status = str((findings.get("regulatory_status") or {}).get("status", "")).lower()
        if status in {"withdrawn", "suspended", "cancelled", "revoked"}:
            flags.append("regulatory_permission_impaired")

        if any(e.get("status") != "absent" for e in findings.get("enforcement", [])):
            flags.append("enforcement_action_on_record")
        if any(s.get("status") != "absent" for s in findings.get("sanctions", [])):
            flags.append("sanctions_exposure")
        return flags
