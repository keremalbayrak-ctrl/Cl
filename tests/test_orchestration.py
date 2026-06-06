import pytest

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.collectors.register import RegisterCollector
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.counterparty import CounterpartyRiskAssessor
from wealth_exposure.exposure_register import ExposureRegister
from wealth_exposure.guardrails import GuardrailViolation, Subject
from wealth_exposure.orchestrator import ExposureRun
from wealth_exposure.registry import CollectorRegistry


class StubAdapter:
    def __init__(self, name):
        self.name = name

    def fetch(self, identifier):
        return [{"register": self.name, "id": identifier}]


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_entity("client-1", "ENT-UK")
    return s


def test_register_collector_is_gated():
    c = RegisterCollector(DEFAULT_ALLOWLIST, _scope(), "uk_companies_house", StubAdapter("CH"))
    assert c.collect(Subject("ENT-UK", "entity"))[0]["source"] == "uk_companies_house"
    with pytest.raises(GuardrailViolation):
        c.collect(Subject("ENT-OTHER", "entity"))


def test_registry_builds_only_automatable_allowlisted():
    built = CollectorRegistry(DEFAULT_ALLOWLIST, _scope(), adapters={
        "uk_companies_house": StubAdapter("a"),   # allowlisted + automatable
        "ky_general_registry": StubAdapter("b"),  # allowlisted, NOT automatable
        "made_up_source": StubAdapter("c"),       # not on allowlist
    }).build()
    assert "uk_companies_house" in built["collectors"]
    assert "ky_general_registry" in built["manual_only"]
    assert "made_up_source" in built["skipped"]


def test_exposure_run_sweeps_only_the_given_clients_subjects():
    scope = _scope()
    scope.add_client(ClientRecord("client-2", verified=True))
    scope.declare_entity("client-2", "ENT-OTHER")  # another client's entity
    collectors = {"uk_companies_house": RegisterCollector(
        DEFAULT_ALLOWLIST, scope, "uk_companies_house", StubAdapter("CH"))}
    out = ExposureRun(scope, ExposureRegister()).run("client-1", entity_collectors=collectors)
    assert {r["subject"] for r in out["records"]} == {"ENT-UK"}


def test_exposure_run_records_counterparty_flags():
    scope = _scope()
    scope.declare_counterparty("client-1", "FIRM")

    class DD:
        def regulatory_status(self, f): return {"status": "authorised"}
        def latest_audit_opinion(self, f): return {"opinion": "qualified"}
        def enforcement_actions(self, f): return []
        def sanctions_hits(self, f): return []

    assessor = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, scope, DD(), sources=["uk_fca_register"])
    register = ExposureRegister()
    out = ExposureRun(scope, register).run("client-1", counterparty_assessor=assessor)
    assert out["counterparties"][0]["firm"] == "FIRM"
    assert any("Counterparty risk" in i.description for i in register.for_client("client-1"))
