import pytest

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST, Source, SourceAllowlist
from wealth_exposure.collectors.base import Collector
from wealth_exposure.collectors.breach_exposure import BreachExposureCollector
from wealth_exposure.collectors.companies_house import CompaniesHouseCollector
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.guardrails import GuardrailViolation, Subject


class StubCH:
    def get_company(self, n): return {"number": n, "name": "Client Co Ltd"}
    def get_officers(self, n): return [{"name": "A. Client", "role": "director"}]
    def get_psc(self, n): return [{"name": "A. Client"}]
    def get_charges(self, n): return []


class StubBreach:
    def check_own_exposure(self, identifier): return [{"breach": "ExampleCorp 2021"}]


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_entity("client-1", "12345678")
    s.declare_identifier("client-1", "client@example.com")
    return s


def test_companies_house_collects_declared_entity():
    c = CompaniesHouseCollector(DEFAULT_ALLOWLIST, _scope(), StubCH())
    out = c.collect(Subject("12345678", "entity"))
    assert out[0]["company"]["number"] == "12345678"


def test_companies_house_rejects_undeclared_entity():
    c = CompaniesHouseCollector(DEFAULT_ALLOWLIST, _scope(), StubCH())
    with pytest.raises(GuardrailViolation):
        c.collect(Subject("99999999", "entity"))


def test_breach_collector_accepts_own_identifier():
    c = BreachExposureCollector(DEFAULT_ALLOWLIST, _scope(), StubBreach())
    out = c.collect(Subject("client@example.com", "identifier"))
    assert out[0]["exposure"] == [{"breach": "ExampleCorp 2021"}]


def test_breach_collector_rejects_third_party_identifier():
    c = BreachExposureCollector(DEFAULT_ALLOWLIST, _scope(), StubBreach())
    with pytest.raises(GuardrailViolation):
        c.collect(Subject("victim@example.com", "identifier"))


def test_absence_recorded_for_empty_fetch():
    class EmptyCollector(Collector):
        source_id = "uk_gazette"

        def _fetch(self, subject):
            return []

    c = EmptyCollector(DEFAULT_ALLOWLIST, _scope())
    out = c.collect(Subject("client-1", "person"))
    assert out == [{"status": "absent", "evidence": None}]


def test_terms_not_permitting_automation_block_collection():
    al = SourceAllowlist([
        Source("no_auto", "Manual-only source", "UK", "misc", False, 60),
    ])

    class NoAutoCollector(Collector):
        source_id = "no_auto"

        def _fetch(self, subject):
            return [{"x": 1}]

    c = NoAutoCollector(al, _scope())
    with pytest.raises(PermissionError):
        c.collect(Subject("client-1", "person"))
