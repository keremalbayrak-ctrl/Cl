import pytest

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.counterparty import CounterpartyRiskAssessor
from wealth_exposure.guardrails import GuardrailViolation


class StubDD:
    def __init__(self, opinion="qualified", going_concern=True,
                 enforcement=None, sanctions=None, status="authorised"):
        self._opinion = opinion
        self._gc = going_concern
        self._enf = enforcement or []
        self._sanc = sanctions or []
        self._status = status

    def regulatory_status(self, firm): return {"status": self._status}
    def latest_audit_opinion(self, firm): return {"opinion": self._opinion, "going_concern": self._gc}
    def enforcement_actions(self, firm): return self._enf
    def sanctions_hits(self, firm): return self._sanc


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_counterparty("client-1", "bybit-entity")
    return s


def test_flags_qualified_audit_opinion_for_declared_counterparty():
    a = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, _scope(), StubDD(),
                                 sources=["uk_fca_register", "uk_companies_house"])
    out = a.assess("bybit-entity")
    assert "adverse_or_qualified_audit_opinion" in out["risk_flags"]
    assert out["client"] == "client-1"
    assert out["label"].startswith("counterparty risk from public sources")


def test_clean_counterparty_has_no_flags():
    dd = StubDD(opinion="unqualified", going_concern=False)
    a = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, _scope(), dd,
                                 sources=["uk_fca_register"])
    assert a.assess("bybit-entity")["risk_flags"] == []


def test_rejects_undeclared_firm():
    a = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, _scope(), StubDD(),
                                 sources=["uk_fca_register"])
    with pytest.raises(GuardrailViolation):
        a.assess("some-random-firm")  # not a declared counterparty


def test_rejects_off_allowlist_source():
    a = CounterpartyRiskAssessor(DEFAULT_ALLOWLIST, _scope(), StubDD(),
                                 sources=["not_a_real_source"])
    with pytest.raises(GuardrailViolation):
        a.assess("bybit-entity")
