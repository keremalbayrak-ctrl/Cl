# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A lawful, **consent-gated** wealth/identity exposure-intelligence pipeline. For a
consenting, identity-verified client and their consenting family, it reads public
and semi-public records about *them*, correlates the findings, infers regulatory
exposure from published rules, and maintains a per-client exposure register so the
client can reduce and monitor what an adversary could lawfully assemble.

## Commands

- Run tests: `python -m pytest`
- Run a single test: `python -m pytest tests/test_guardrails.py::test_absence_is_recorded_not_inferred`
- Run the end-to-end demo (stub providers, no network): `python examples/demo.py`

Python 3.10+. No third-party runtime dependencies; tests use `pytest`
(`pip install -e ".[dev]"` or `pip install pytest`).

## Architecture

The design puts the safety constraints at the boundary so later features cannot
bypass them:

- `wealth_exposure/guardrails.py` — the five hard constraints as code
  (`assert_in_consent_scope`, `assert_source_allowed`, `assert_own_identifier_only`,
  `record_absence_not_presence`). Everything routes through these.
- `wealth_exposure/consent.py` — `ConsentScope`: the single source of truth for
  who/what may be queried. `covers()` is the gate. Clients must be verified;
  data is declared per verified client.
- `wealth_exposure/allowlist.py` — `SourceAllowlist` of official registers /
  licensed providers; `terms_permit_automation` is checked before collection.
- `wealth_exposure/collectors/base.py` — `Collector` ABC: enforces allowlist +
  consent + rate limit before any `_fetch`. Concrete collectors:
  `companies_house.py` (client's own entities), `breach_exposure.py`
  (client's own identifiers only).
- `wealth_exposure/resolver.py` — correlation with a two-source confirmation rule.
- `wealth_exposure/inference/regulatory_scope.py` — probability a *firm* is in a
  published rule's scope, from public attributes; output labelled
  "unconfirmed by firm".
- `wealth_exposure/exposure_register.py` — per-client living record.
- `wealth_exposure/watchers/base.py` — foresight watcher interface.

## Non-negotiable invariants (do not weaken)

1. Consent-gated to the verified client/family; reject any non-client subject.
2. Lawful, allowlisted, disclosable sources only.
3. No third-party surveillance or profiling.
4. No non-public/stolen/leaked third-party data; breach checks take the client's
   own identifiers only.
5. No fabricated outputs; record absence, never infer presence.

There is intentionally **no entry point that accepts an arbitrary third-party
target**. Do not add one, and do not remove the consent gate, the allowlist, or
the own-data-only breach restriction — these are the product, not an obstacle.
