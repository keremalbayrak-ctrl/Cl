"""Lawful source allowlist.

Collectors may only call a source listed here, and only when its terms permit
automated collection. Public availability does not by itself permit automated
bulk collection — `terms_permit_automation` records that judgement per source,
and `rate_limit_per_min` is honoured by the base collector.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    source_id: str
    name: str
    jurisdiction: str
    category: str
    terms_permit_automation: bool
    rate_limit_per_min: int


class SourceAllowlist:
    def __init__(self, sources):
        self._by_id = {s.source_id: s for s in sources}

    def contains(self, source_id) -> bool:
        return source_id in self._by_id

    def get(self, source_id) -> Source:
        return self._by_id[source_id]


# Official registers and licensed providers only. Extend with additional
# official sources as collectors are added; never add an off-register, scraped
# (against terms), or leaked source.
DEFAULT_ALLOWLIST = SourceAllowlist([
    Source("uk_companies_house", "Companies House", "UK", "corporate", True, 600),
    Source("uk_land_registry", "HM Land Registry", "UK", "property", True, 60),
    Source("uk_fca_register", "FCA Register", "UK", "regulator", True, 120),
    Source("uk_gazette", "The Gazette", "UK", "gazette", True, 60),
    Source("uk_insolvency", "Insolvency Register", "UK", "court", True, 60),
    Source("ofsi_sanctions", "UK OFSI consolidated list", "UK", "sanctions", True, 60),
    Source("breach_licensed_provider", "Licensed exposure provider", "GLOBAL",
           "breach_licensed", True, 60),
])
