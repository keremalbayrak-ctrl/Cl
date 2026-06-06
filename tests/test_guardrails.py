import pytest

from wealth_exposure.allowlist import DEFAULT_ALLOWLIST
from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.guardrails import (
    GuardrailViolation,
    Subject,
    assert_in_consent_scope,
    assert_own_identifier_only,
    assert_source_allowed,
    record_absence_not_presence,
)


def _scope():
    s = ConsentScope()
    s.add_client(ClientRecord("client-1", verified=True))
    s.declare_entity("client-1", "12345678")
    s.declare_identifier("client-1", "client@example.com")
    return s


def test_subject_rejects_unknown_kind():
    with pytest.raises(ValueError):
        Subject("x", "wealth")


def test_subject_rejects_empty_identifier():
    with pytest.raises(ValueError):
        Subject("", "person")


def test_consent_scope_rejects_non_client():
    with pytest.raises(GuardrailViolation):
        assert_in_consent_scope(Subject("someone-else", "person"), _scope())


def test_consent_scope_rejects_undeclared_entity():
    with pytest.raises(GuardrailViolation):
        assert_in_consent_scope(Subject("99999999", "entity"), _scope())


def test_consent_scope_allows_declared_entity():
    assert_in_consent_scope(Subject("12345678", "entity"), _scope())  # no raise


def test_source_allowlist_rejects_off_list():
    with pytest.raises(GuardrailViolation):
        assert_source_allowed("some_random_source", DEFAULT_ALLOWLIST)


def test_breach_rejects_third_party_identifier():
    with pytest.raises(GuardrailViolation):
        assert_own_identifier_only("victim@example.com", _scope())


def test_breach_allows_own_identifier():
    assert_own_identifier_only("client@example.com", _scope())  # no raise


def test_absence_is_recorded_not_inferred():
    assert record_absence_not_presence([]) == [{"status": "absent", "evidence": None}]
    assert record_absence_not_presence([{"x": 1}]) == [{"x": 1}]
