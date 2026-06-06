"""Regulatory-scope inference.

Given a published rule's scope criteria and a firm's PUBLIC register attributes,
estimate the probability that the firm falls within the rule's scope. The output
is always labelled "unconfirmed by firm": it is a public-records inference about
a regulated firm, not a statement of fact, and not anything about an individual.

Lawful because every input is public (the published rule + the firm's register
entry) and the output is clearly labelled as inference. The maths never launders
unlawful inputs; the guardrails reject those before they reach it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleScope:
    rule_id: str
    required_attributes: dict  # e.g. {"permission": "emoney_institution"}


def probability_in_scope(rule: RuleScope, firm_register_attrs: dict) -> dict:
    required = rule.required_attributes
    matched = [k for k, v in required.items() if firm_register_attrs.get(k) == v]
    missing = [k for k in required if k not in matched]
    p = len(matched) / max(len(required), 1)
    return {
        "rule": rule.rule_id,
        "probability_in_scope": round(p, 3),
        "matched_attributes": matched,
        "missing_attributes": missing,
        "label": "in scope on public criteria, unconfirmed by firm",
        "basis": "published rule scope + public register attributes",
    }
