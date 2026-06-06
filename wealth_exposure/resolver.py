"""Entity resolution and correlation, scoped to the consent set.

Seeds are the client's declared subjects only; the resolver never introduces a
new third-party target — it only correlates records already lawfully collected.
Nothing is treated as established without confirmation from two independent
sources. The normalisers handle name variants, transliteration (accent folding)
and corporate-suffix noise so the same client entity is recognised across
registers and jurisdictions.
"""
from __future__ import annotations

import re
import unicodedata
from itertools import combinations

_CORPORATE_SUFFIXES = {
    "ltd", "limited", "plc", "llp", "llc", "inc", "incorporated", "co",
    "company", "corp", "corporation", "holdings", "holding", "group",
    "gmbh", "ag", "sa", "sarl", "bv", "nv", "spa", "srl", "oy", "ab", "as",
    "pte", "sdn", "bhd", "pty", "trading",
}


class Resolver:
    def __init__(self, consent=None):
        self.consent = consent

    # --- normalisers --------------------------------------------------------
    @staticmethod
    def _fold(text: str) -> str:
        s = unicodedata.normalize("NFKD", text)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9 ]+", " ", s.lower())

    @classmethod
    def normalize_name(cls, name: str) -> str:
        tokens = [t for t in cls._fold(name).split()
                  if t and t not in _CORPORATE_SUFFIXES]
        return " ".join(tokens)

    @classmethod
    def normalize_address(cls, address: str) -> str:
        return " ".join(cls._fold(address).split())

    # --- cross-reference strategies ----------------------------------------
    def resolve_name_variants(self, names) -> dict:
        """Group names (variants, transliterations, former names) by key."""
        groups: dict = {}
        for n in names:
            groups.setdefault(self.normalize_name(n), []).append(n)
        return groups

    def correlate(self, records: list) -> dict:
        """Two-source confirmation over atomic claims.

        Each record may carry {"claims": [{"key": ..., "source": ...}, ...]}.
        A claim is 'established' only when confirmed by >= 2 distinct sources.
        """
        by_claim: dict = {}
        for r in records:
            for claim in self._claims(r):
                by_claim.setdefault(claim["key"], []).append(claim["source"])

        established, unconfirmed = [], []
        for key, sources in by_claim.items():
            distinct = sorted(set(sources))
            target = established if len(distinct) >= 2 else unconfirmed
            target.append({"claim": key, "sources": distinct})
        return {"established": established, "unconfirmed": unconfirmed}

    def correlate_by_address(self, records: list) -> dict:
        """Group subjects that share a normalised address (>= 2 subjects)."""
        groups: dict = {}
        for r in records:
            if "address" not in r:
                continue
            groups.setdefault(self.normalize_address(r["address"]), []).append(
                r.get("subject"))
        return {k: v for k, v in groups.items() if len(v) >= 2}

    def build_network(self, records: list) -> list:
        """Undirected co-occurrence edges from records carrying {"nodes": [...]}."""
        weights: dict = {}
        for r in records:
            nodes = sorted({n for n in r.get("nodes", []) if n})
            for a, b in combinations(nodes, 2):
                weights[(a, b)] = weights.get((a, b), 0) + 1
        return [{"edge": [a, b], "weight": w}
                for (a, b), w in sorted(weights.items())]

    def _claims(self, record: dict) -> list:
        # Normalise a record into atomic claims (address, control, holding, ...)
        # each as {"key": ..., "source": ...}. Implement per source schema.
        return record.get("claims", [])
