import pytest

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.collectors.sanctions_screening import SanctionsScreeningCollector
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.guardrails import GuardrailViolation, Subject


class StubScreen:
    def screen(self, identifier, source_id):
        return []  # no match


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_entity("client-1", "ENT")
    return s


def test_screens_own_person():
    c = SanctionsScreeningCollector(DEFAULT_ALLOWLIST, _scope(), "ofsi_sanctions", StubScreen())
    out = c.collect(Subject("client-1", "person"))
    assert out[0]["subject"] == "client-1"
    assert out[0]["matches"] == []


def test_rejects_third_party_subject():
    c = SanctionsScreeningCollector(DEFAULT_ALLOWLIST, _scope(), "ofsi_sanctions", StubScreen())
    with pytest.raises(GuardrailViolation):
        c.collect(Subject("random-person", "person"))


def test_rejects_off_allowlist_list():
    c = SanctionsScreeningCollector(DEFAULT_ALLOWLIST, _scope(), "not_a_list", StubScreen())
    with pytest.raises(GuardrailViolation):
        c.collect(Subject("client-1", "person"))
