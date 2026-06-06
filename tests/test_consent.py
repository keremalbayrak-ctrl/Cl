import pytest

from wealth_exposure.consent import ClientRecord, ConsentScope
from wealth_exposure.guardrails import Subject


def test_add_client_requires_verification():
    scope = ConsentScope()
    with pytest.raises(ValueError):
        scope.add_client(ClientRecord("client-1", verified=False))


def test_declare_requires_known_client():
    scope = ConsentScope()
    with pytest.raises(ValueError):
        scope.declare_entity("ghost", "12345678")


def test_covers_each_kind():
    scope = ConsentScope()
    scope.add_client(ClientRecord("client-1", verified=True))
    scope.declare_entity("client-1", "ENT")
    scope.declare_asset("client-1", "ASSET")
    scope.declare_identifier("client-1", "ID")
    assert scope.covers(Subject("client-1", "person"))
    assert scope.covers(Subject("ENT", "entity"))
    assert scope.covers(Subject("ASSET", "asset"))
    assert scope.covers(Subject("ID", "identifier"))
    assert not scope.covers(Subject("other", "person"))
