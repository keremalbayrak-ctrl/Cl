"""Official Companies House API collector.

The subject must be a company the client has declared as their own; the base
class enforces that before this runs. It reads public filing data (company,
officers, PSC, charges) about the client's own entity. The injected
`api_client` wraps the official API and key, honouring its rate limits and
terms of use.
"""
from __future__ import annotations

from ..guardrails import Subject
from .base import Collector


class CompaniesHouseCollector(Collector):
    source_id = "uk_companies_house"

    def __init__(self, allowlist, consent, api_client):
        super().__init__(allowlist, consent)
        self.api = api_client

    def _fetch(self, subject: Subject) -> list:
        if subject.kind != "entity":
            return []
        company = self.api.get_company(subject.identifier)
        officers = self.api.get_officers(subject.identifier)
        psc = self.api.get_psc(subject.identifier)
        charges = self.api.get_charges(subject.identifier)
        return [{
            "source": self.source_id,
            "entity": subject.identifier,
            "company": company,
            "officers": officers,
            "psc": psc,
            "charges": charges,
        }]
