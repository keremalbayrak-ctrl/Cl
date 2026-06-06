"""Hard constraints, enforced in code.

These functions are the product: every collector and inference path must pass
through them. They reject any operation that would breach one of the five
constraints (see README). They are deliberately small and dependency-free so
they cannot be quietly bypassed by a later feature.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

ALLOWED_KINDS = frozenset({"person", "entity", "asset", "identifier", "counterparty"})


class GuardrailViolation(Exception):
    """Raised when an operation would breach a hard constraint."""


@dataclass(frozen=True)
class Subject:
    """A thing a query is about.

    Always the consenting client/family, or an entity/asset/identifier the
    client has declared as their own, or a "counterparty" firm the client
    holds assets with (their own relationship, for firm-level due diligence).
    There is no representation here for an arbitrary third-party target, by
    design.
    """

    identifier: str
    kind: str  # one of ALLOWED_KINDS

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_KINDS:
            raise ValueError(f"Unknown subject kind: {self.kind!r}")
        if not self.identifier:
            raise ValueError("Subject identifier must be non-empty.")


@runtime_checkable
class ConsentScopeLike(Protocol):
    def covers(self, subject: "Subject") -> bool: ...
    def is_own_identifier(self, identifier: str) -> bool: ...


@runtime_checkable
class AllowlistLike(Protocol):
    def contains(self, source_id: str) -> bool: ...


def assert_in_consent_scope(subject: Subject, consent: ConsentScopeLike) -> None:
    """Constraints 1 and 3: the subject must be the consenting client/family or
    an entity/asset/identifier the client declared as their own."""
    if not consent.covers(subject):
        raise GuardrailViolation(
            f"Subject {subject.kind}:{subject.identifier} is not within the "
            f"consent scope. The system does not query non-clients."
        )


def assert_source_allowed(source_id: str, allowlist: AllowlistLike) -> None:
    """Constraint 2: only sources on the lawful allowlist may be queried."""
    if not allowlist.contains(source_id):
        raise GuardrailViolation(f"Source {source_id!r} is not on the allowlist.")


def assert_own_identifier_only(identifier: str, consent: ConsentScopeLike) -> None:
    """Constraint 4: breach/leak checks accept only the client's OWN declared
    identifiers, via licensed providers. No raw leaked database is ever queried,
    and no third-party identifier is ever accepted."""
    if not consent.is_own_identifier(identifier):
        raise GuardrailViolation(
            "Breach/exposure checks accept only the client's own declared "
            "identifiers. Third-party or undeclared identifiers are refused."
        )


def record_absence_not_presence(results: list) -> list:
    """Constraint 5: a source that returns nothing yields a recorded absence,
    never an inferred presence."""
    return results if results else [{"status": "absent", "evidence": None}]
