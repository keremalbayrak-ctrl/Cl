# Wealth-Exposure Intelligence (consent-gated)

A lawful, consent-gated pipeline that shows a **consenting, identity-verified
client and their consenting family** the exposure an adversary could lawfully
assemble about *them*, from public and semi-public records — so they can reduce
and monitor it.

It reads official registers and licensed providers, correlates what it finds,
infers what is coming from published rules, and maintains a per-client exposure
register.

## The invariant that makes this defensible

Every query is seeded from the client's own declared data and scoped to the
consenting client/family. **There is no entry point that accepts an arbitrary
third-party target.** This is enforced in code (`guardrails.py`, `consent.py`),
not just documented.

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

## Layout

| Module | Role |
| --- | --- |
| `wealth_exposure/guardrails.py` | The hard constraints, as code. Everything routes through here. |
| `wealth_exposure/consent.py` | `ConsentScope` — the source of truth for who/what may be queried. |
| `wealth_exposure/allowlist.py` | The lawful source allowlist + per-source automation/rate-limit policy. |
| `wealth_exposure/collectors/` | One collector per source (`companies_house`, own-data `breach_exposure`), all gated by `base.py`. |
| `wealth_exposure/resolver.py` | Correlation with a two-source confirmation rule. |
| `wealth_exposure/inference/regulatory_scope.py` | Firm-in-scope inference from published rules + public register attributes (labelled "unconfirmed by firm"). |
| `wealth_exposure/exposure_register.py` | Per-client living record. |
| `wealth_exposure/watchers/` | Foresight watcher interface. |

## Run

```bash
python -m pytest          # guardrail + module tests
python examples/demo.py   # end-to-end demo with stub providers (no network)
```

Real source integrations must use each source's official API/feed and respect
its terms of use and rate limits; public availability does not by itself permit
automated bulk collection.
