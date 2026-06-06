"""Consent scope: the single source of truth for who/what may be queried.

Every query is seeded from data recorded here, and `covers()` is the gate that
`guardrails.assert_in_consent_scope` checks. Family members are added as their
own verified clients, each with their own consent record. Data (entities,
assets, identifiers, counterparties) can only be declared for a client already
verified and in scope, and each declaration records which client it belongs to
so findings can be attributed back to a client (`owner_of`).
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
    clients: dict = field(default_factory=dict)                  # person_id -> ClientRecord
    declared_entities: dict = field(default_factory=dict)        # entity_id -> owner client_id
    declared_assets: dict = field(default_factory=dict)          # asset_id -> owner client_id
    own_identifiers: dict = field(default_factory=dict)          # identifier -> owner client_id
    declared_counterparties: dict = field(default_factory=dict)  # firm_id -> owner client_id

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
        self.declared_entities[entity_id] = client_id

    def declare_asset(self, client_id: str, asset_id: str) -> None:
        self._require_client(client_id)
        self.declared_assets[asset_id] = client_id

    def declare_identifier(self, client_id: str, identifier: str) -> None:
        self._require_client(client_id)
        self.own_identifiers[identifier] = client_id

    def declare_counterparty(self, client_id: str, firm_id: str) -> None:
        """Record a firm the client holds assets with (their own relationship),
        making it eligible for firm-level counterparty due diligence."""
        self._require_client(client_id)
        self.declared_counterparties[firm_id] = client_id

    def covers(self, subject: Subject) -> bool:
        table = self._table(subject.kind)
        return table is not None and subject.identifier in table

    def is_own_identifier(self, identifier: str) -> bool:
        return identifier in self.own_identifiers

    def owner_of(self, subject: Subject):
        """Return the client_id that owns/declared this subject, or None."""
        if subject.kind == "person":
            return subject.identifier if subject.identifier in self.clients else None
        table = self._table(subject.kind)
        return None if table is None else table.get(subject.identifier)

    def _table(self, kind: str):
        return {
            "person": self.clients,
            "entity": self.declared_entities,
            "asset": self.declared_assets,
            "identifier": self.own_identifiers,
            "counterparty": self.declared_counterparties,
        }.get(kind)
