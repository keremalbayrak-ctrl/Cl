"""Runnable demo with stub providers — no network, no real data.

Wires the expanded pipeline for one consenting client: own-entity register read,
own-data breach check, own-identity sanctions screening, counterparty due
diligence (firm-level), foresight watchers (early detection), and
cross-referencing — then shows the guardrail refusing an out-of-scope query.
"""
from __future__ import annotations

import os
import sys

# Make the package importable when run directly as `python examples/demo.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.collectors.breach_exposure import BreachExposureCollector
from wealth_exposure.collectors.companies_house import CompaniesHouseCollector
from wealth_exposure.collectors.sanctions_screening import SanctionsScreeningCollector
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.counterparty import CounterpartyRiskAssessor
from wealth_exposure.exposure_register import ExposureItem, ExposureRegister
from wealth_exposure.guardrails import GuardrailViolation, Subject
from wealth_exposure.inference.regulatory_scope import RuleScope, probability_in_scope
from wealth_exposure.orchestrator import ExposureRun
from wealth_exposure.registry import CollectorRegistry
from wealth_exposure.resolver import Resolver
from wealth_exposure.watchers.feeds import CounterpartyFilingWatcher, RegisterChangeWatcher
from wealth_exposure.watchers.runner import WatcherRunner


class StubCompaniesHouseAPI:
    def get_company(self, n): return {"number": n, "name": "Client Holdings Ltd", "status": "active"}
    def get_officers(self, n): return [{"name": "A. Client", "role": "director"}]
    def get_psc(self, n): return [{"name": "A. Client", "kind": "individual-person-with-significant-control"}]
    def get_charges(self, n): return [{"lender": "Example Bank plc", "status": "outstanding"}]


class StubBreachProvider:
    def check_own_exposure(self, identifier):
        return [{"breach": "ExampleCorp 2021", "data": ["email", "password_hash"]}]


class StubScreening:
    def screen(self, identifier, source_id): return []  # no sanctions / PEP match


class StubCounterpartyDD:
    def regulatory_status(self, firm): return {"status": "authorised", "regulator": "FCA"}
    def latest_audit_opinion(self, firm): return {"opinion": "qualified", "going_concern": True, "year": 2025}
    def enforcement_actions(self, firm): return []
    def sanctions_hits(self, firm): return []


class StubFeed:
    def __init__(self, changes): self._changes = changes
    def poll(self): return self._changes


def main() -> None:
    print(f"Lawful source catalogue: {len(DEFAULT_ALLOWLIST)} sources "
          f"({len(DEFAULT_ALLOWLIST.automatable())} automatable)\n")

    # Consent scope: one verified client; their own entity, identifier, counterparty.
    consent = ConsentScope()
    consent.add_client(ClientRecord("client-1", verified=True))
    consent.declare_entity("client-1", "12345678")
    consent.declare_identifier("client-1", "client@example.com")
    consent.declare_counterparty("client-1", "bybit-fzco")  # a firm the client uses

    register = ExposureRegister()

    # Own entity: public company filing.
    ch = CompaniesHouseCollector(DEFAULT_ALLOWLIST, consent, StubCompaniesHouseAPI())
    for rec in ch.collect(Subject("12345678", "entity")):
        if rec.get("charges"):
            register.add(ExposureItem("client-1", "uk_companies_house",
                                      "Outstanding charge reveals lender / leverage",
                                      evidence={"charges": rec["charges"]}))

    # Own identifier: breach exposure (own data only).
    breach = BreachExposureCollector(DEFAULT_ALLOWLIST, consent, StubBreachProvider())
    for rec in breach.collect(Subject("client@example.com", "identifier")):
        if rec.get("exposure"):
            register.add(ExposureItem("client-1", "breach_licensed_provider",
                                      "Client credential found in known breach",
                                      evidence={"exposure": rec["exposure"]}))

    # Own identity: sanctions / PEP screening (own status only).
    screen = SanctionsScreeningCollector(DEFAULT_ALLOWLIST, consent, "ofsi_sanctions", StubScreening())
    print("Sanctions screening (own):", screen.collect(Subject("client-1", "person"))[0])

    # Counterparty due diligence (firm-level, public sources only).
    assessor = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, consent, StubCounterpartyDD(),
                                        sources=["uk_fca_register", "uk_companies_house"])
    cp = assessor.assess("bybit-fzco")
    print("Counterparty risk:", cp["firm"], cp["risk_flags"])
    for flag in cp["risk_flags"]:
        register.add(ExposureItem("client-1", "counterparty_dd",
                                  f"Counterparty risk: {flag} ({cp['firm']})",
                                  evidence={"assessment": cp}))

    # Regulatory-scope inference about a FIRM (public criteria only).
    rule = RuleScope("FCA-PS25-12-safeguarding", {"permission": "emoney_institution"})
    print("Reg-scope inference:", probability_in_scope(rule, {"permission": "emoney_institution"})["label"])

    # Full multi-jurisdiction sweep: one generic collector, many registers, one
    # orchestrated run — all gated to the client's own declared subjects.
    class StubAdapter:
        def __init__(self, name): self.name = name
        def fetch(self, identifier): return [{"register": self.name, "id": identifier}]

    built = CollectorRegistry(DEFAULT_ALLOWLIST, consent, adapters={
        "uk_companies_house": StubAdapter("Companies House"),
        "us_sec_edgar": StubAdapter("SEC EDGAR"),
        "fr_inpi_rne": StubAdapter("INPI RNE"),
        "ky_general_registry": StubAdapter("Cayman GR"),  # not automatable -> manual only
    }).build()
    swept = ExposureRun(consent, register).run("client-1", entity_collectors=built["collectors"])
    print(f"Full sweep: {len(built['collectors'])} automatable registers, "
          f"manual-only={built['manual_only']}, records={len(swept['records'])}")

    # Foresight watchers (early detection), scoped to the client.
    register_feed = StubFeed([
        {"entity": "12345678", "summary": "New PSC filing on client's entity"},
        {"entity": "99999999", "summary": "Change on an unrelated entity"},  # ignored
    ])
    cp_feed = StubFeed([{"firm": "bybit-fzco", "summary": "Qualified audit opinion filed"}])
    WatcherRunner([
        RegisterChangeWatcher(DEFAULT_ALLOWLIST, consent, register_feed),
        CounterpartyFilingWatcher(DEFAULT_ALLOWLIST, consent, cp_feed),
    ], register).run_once()

    # Cross-referencing: name variants + co-occurrence network.
    resolver = Resolver(consent)
    print("Name variants:", resolver.resolve_name_variants(
        ["Açme Holdings Ltd", "ACME, Inc.", "Beta Trading LLC"]))
    print("Network edges:", resolver.build_network(
        [{"nodes": ["A. Client", "12345678", "1 High St"]}]))

    # Guardrail in action: an out-of-scope query is refused.
    try:
        ch.collect(Subject("99999999", "entity"))
    except GuardrailViolation as e:
        print("Refused (as designed):", e)

    print("\nExposure register for client-1:")
    for item in register.for_client("client-1"):
        print(" -", item.description, f"[{item.status}]")


if __name__ == "__main__":
    main()
