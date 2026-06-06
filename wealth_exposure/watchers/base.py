"""Foresight watcher interface.

Each concrete watcher wraps a public feed (regulator publications, register
status, sanctions/listing changes), detects a change, maps it to the affected
consent-scoped subjects, and produces exposure-register flags. The same five
constraints apply: changes are read from public feeds, and only consent-scoped
subjects are ever flagged.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..exposure_register import ExposureItem


class Watcher(ABC):
    """Wraps one public feed and turns changes into consent-scoped flags."""

    feed_id: str

    def __init__(self, allowlist, consent):
        self.allowlist = allowlist
        self.consent = consent

    @abstractmethod
    def detect_changes(self) -> list:
        """Return changes observed on the public feed since the last poll."""
        raise NotImplementedError

    @abstractmethod
    def map_to_subjects(self, change: dict) -> list:
        """Map a change to affected subjects that are within consent scope.

        Implementations must only return consent-scoped subjects; a change that
        touches no in-scope subject yields an empty list.
        """
        raise NotImplementedError

    def to_exposure_items(self, change: dict) -> list:
        """Turn a change into exposure-register items, re-checking scope.

        `subject_to_client_id` resolves the owning client; the default assumes
        the subject is the client (person). Override for entity/asset subjects
        once the consent scope records ownership links.
        """
        items = []
        for subject in self.map_to_subjects(change):
            if not self.consent.covers(subject):
                continue  # belt-and-braces: never flag a non-client
            items.append(ExposureItem(
                client_id=self.subject_to_client_id(subject),
                source=self.feed_id,
                description=change.get("summary", "change detected"),
                evidence={"change": change},
            ))
        return items

    def subject_to_client_id(self, subject) -> str:
        return subject.identifier
