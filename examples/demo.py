"""Runnable demo with stub providers — no network, no real data.

Shows the pipeline wired up for a single consenting client, and shows the
guardrail refusing an out-of-scope query.
"""
from __future__ import annotations

import os
import sys

# Make the package importable when run directly as `python examples/demo.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.collectors.breach_exposure import BreachExposureCollector
from wealth_exposure.collectors.companies_house import CompaniesHouseCollector
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.exposure_register import ExposureItem, ExposureRegister
from wealth_exposure.guardrails import GuardrailViolation, Subject
from wealth_exposure.inference.regulatory_scope import RuleScope, probability_in_scope


class StubCompaniesHouseAPI:
    def get_company(self, n):
        return {"number": n, "name": "Client Holdings Ltd", "status": "active"}

    def get_officers(self, n):
        return [{"name": "A. Client", "role": "director"}]

    def get_psc(self, n):
        return [{"name": "A. Client",
                 "kind": "individual-person-with-significant-control"}]

    def get_charges(self, n):
        return [{"lender": "Example Bank plc", "status": "outstanding"}]


class StubLicensedBreachProvider:
    def check_own_exposure(self, identifier):
        return [{"breach": "ExampleCorp 2021", "data": ["email", "password_hash"]}]


def main() -> None:
    # 1. Consent scope: one verified client, their own entity + own identifier.
    consent = ConsentScope()
    consent.add_client(ClientRecord("client-1", verified=True))
    consent.declare_entity("client-1", "12345678")
    consent.declare_identifier("client-1", "client@example.com")

    register = ExposureRegister()

    # 2. Read the client's OWN company filing (public data about their entity).
    ch = CompaniesHouseCollector(DEFAULT_ALLOWLIST, consent, StubCompaniesHouseAPI())
    for rec in ch.collect(Subject("12345678", "entity")):
        print("Companies House:", rec)
        if rec.get("charges"):
            register.add(ExposureItem(
                client_id="client-1",
                source="uk_companies_house",
                description="Outstanding charge reveals lender / leverage",
                evidence={"charges": rec["charges"]},
            ))

    # 3. Check the client's OWN identifier for breach exposure (own data only).
    breach = BreachExposureCollector(DEFAULT_ALLOWLIST, consent,
                                     StubLicensedBreachProvider())
    for rec in breach.collect(Subject("client@example.com", "identifier")):
        print("Breach (own data):", rec)
        if rec.get("exposure"):
            register.add(ExposureItem(
                client_id="client-1",
                source="breach_licensed_provider",
                description="Client credential found in known breach",
                evidence={"exposure": rec["exposure"]},
            ))

    # 4. Regulatory-scope inference about a FIRM, from public criteria only.
    rule = RuleScope("FCA-PS25-12-safeguarding", {"permission": "emoney_institution"})
    firm_public_attrs = {"permission": "emoney_institution"}
    print("Reg-scope inference:", probability_in_scope(rule, firm_public_attrs))

    # 5. The guardrail in action: an out-of-scope query is refused.
    try:
        ch.collect(Subject("99999999", "entity"))  # not declared by the client
    except GuardrailViolation as e:
        print("Refused (as designed):", e)

    print("\nExposure register for client-1:")
    for item in register.for_client("client-1"):
        print(" -", item.description, f"[{item.status}]")


if __name__ == "__main__":
    main()
