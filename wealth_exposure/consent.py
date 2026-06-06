"""Consent scope: the single source of truth for who/what may be queried.

Every query is seeded from data recorded here, and `covers()` is the gate that
`guardrails.assert_in_consent_scope` checks. Family members are added as their
own verified clients, each with their own consent record. Data (entities,
assets, identifiers) can only be declared for a client already verified and in
scope.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .guardrails import Subject


@dataclass
class ClientRecord:
    person_id: str
    verified: bool = False


@dataclass
class ConsentScope:
    clients: dict = field(default_factory=dict)
    declared_entities: set = field(default_factory=set)
    declared_assets: set = field(default_factory=set)
    own_identifiers: set = field(default_factory=set)

    def add_client(self, record: ClientRecord) -> None:
        if not record.verified:
            raise ValueError("Client must be identity-verified before being added.")
        self.clients[record.person_id] = record

    def _require_client(self, client_id: str) -> None:
        if client_id not in self.clients:
            raise ValueError(
                f"Unknown client {client_id!r}; declare data only for a "
                f"verified client already in scope."
            )

    def declare_entity(self, client_id: str, entity_id: str) -> None:
        self._require_client(client_id)
        self.declared_entities.add(entity_id)

    def declare_asset(self, client_id: str, asset_id: str) -> None:
        self._require_client(client_id)
        self.declared_assets.add(asset_id)

    def declare_identifier(self, client_id: str, identifier: str) -> None:
        self._require_client(client_id)
        self.own_identifiers.add(identifier)

    def covers(self, subject: Subject) -> bool:
        if subject.kind == "person":
            return subject.identifier in self.clients
        if subject.kind == "entity":
            return subject.identifier in self.declared_entities
        if subject.kind == "asset":
            return subject.identifier in self.declared_assets
        if subject.kind == "identifier":
            return subject.identifier in self.own_identifiers
        return False

    def is_own_identifier(self, identifier: str) -> bool:
        return identifier in self.own_identifiers
