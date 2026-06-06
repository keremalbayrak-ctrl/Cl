# Wealth-Exposure Intelligence (consent-gated)

A lawful, consent-gated pipeline that shows a **consenting, identity-verified
client and their consenting family** the exposure an adversary could lawfully
assemble about *them*, from public and semi-public records — so they can reduce
and monitor it.

It reads official registers and licensed providers, correlates what it finds,
infers what is coming from published rules, runs early-detection watchers, and
maintains a per-client exposure register.

## The invariant that makes this defensible

Every query is seeded from the client's own declared data and scoped to the
consenting client/family. **There is no entry point that accepts an arbitrary
third-party target.** This is enforced in code (`guardrails.py`, `consent.py`),
not just documented. Expanding the source catalogue does not change this — a
bigger allowlist only means more lawful public records can be read *about the
client*, never about a non-client.

## The five constraints (enforced, not aspirational)

1. **Consent-gated** to the verified client and consenting family. Any query
   whose subject is not in the consent scope is rejected.
2. **Lawful, disclosable sources only**, on an enforced allowlist; collection
   only where a source's terms permit automation.
3. **No surveillance or profiling of third parties.**
4. **No non-public, stolen, or leaked third-party data.** Breach/leak checks
   accept *only the client's own declared identifiers*, via licensed providers.
5. **No fabricated outputs.** A source that returns nothing yields a recorded
   absence, never an inferred presence.

## What this is NOT

- Not a way to find "where wealth is held" for people who have not consented.
- Not a third-party lookup, locator, or profiler.
- Not a consumer of leaked/breached databases for discovery. The only breach
  data used is the subject's own, via a licensed provider.

These are not limits bolted on afterwards; the consent gate and the allowlist
are the product.

## Capabilities

- **Source catalogue** (`allowlist.py`) — ~90 official registers / regulator
  registers / licensed providers across the UK, US, EU, Asia, Middle East and
  offshore centres, organised by jurisdiction and category. Each carries a
  conservative `terms_permit_automation` flag; paid or access-restricted sources
  are marked non-automatable so the base collector refuses to bulk-collect them
  until integrated under their actual terms.
- **Collectors** — Companies House (client's own entities), own-data breach
  exposure, and own-identity sanctions/PEP screening. All gated by `base.py`.
- **Counterparty due diligence** (`counterparty.py`) — *firm-level* public due
  diligence on firms the client holds assets with (declared counterparties):
  regulatory status, filed audit opinion, enforcement, sanctions. Surfaces
  early-warning flags (e.g. qualified/adverse opinion, going concern). It is
  anchored to the client's own holdings — **not** third-party profiling and
  **not** a route to a firm's owners or anyone's wealth.
- **Cross-referencing** (`resolver.py`) — name-variant/transliteration
  resolution, address correlation, co-occurrence network mapping, with a
  two-source confirmation rule. Correlates only records already collected.
- **Regulatory-scope inference** (`inference/regulatory_scope.py`) — probability
  a *firm* is in a published rule's scope, from public register attributes,
  labelled "unconfirmed by firm".
- **Foresight watchers** (`watchers/`) — register changes, counterparty
  filings, sanctions-list updates → flags, each scoped to the client.
- **Full run** (`registry.py`, `orchestrator.py`, `collectors/register.py`) — a
  generic `RegisterCollector` covers any allowlisted source via an adapter; the
  `CollectorRegistry` builds collectors for every automatable source (others are
  flagged manual-only); `ExposureRun` sweeps all of a client's own subjects in
  one call. Adding a country is configuration, not bespoke code.
- **Exposure register** (`exposure_register.py`) — per-client living record.

## Layout

| Module | Role |
| --- | --- |
| `wealth_exposure/guardrails.py` | The hard constraints, as code. Everything routes through here. |
| `wealth_exposure/consent.py` | `ConsentScope` — source of truth for who/what may be queried; owner attribution. |
| `wealth_exposure/allowlist.py` | The lawful source catalogue + per-source automation/rate-limit policy. |
| `wealth_exposure/collectors/` | `base.py` gate + `companies_house`, `breach_exposure`, `sanctions_screening`. |
| `wealth_exposure/counterparty.py` | Firm-level counterparty due diligence (declared counterparties only). |
| `wealth_exposure/resolver.py` | Cross-referencing with a two-source confirmation rule. |
| `wealth_exposure/inference/regulatory_scope.py` | Firm-in-scope inference (labelled "unconfirmed by firm"). |
| `wealth_exposure/watchers/` | Foresight watcher interface + concrete watchers + runner. |
| `wealth_exposure/exposure_register.py` | Per-client living record. |

## Run

```bash
python -m pytest          # 45 guardrail + module tests
python examples/demo.py   # end-to-end demo with stub providers (no network)
```

Real source integrations must use each source's official API/feed and respect
its terms of use and rate limits; public availability does not by itself permit
automated bulk collection.
