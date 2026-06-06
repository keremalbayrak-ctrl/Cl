# Wealth-Exposure Intelligence — Developer Handoff & Build Recommendations

This is the single document to hand to a web developer. It describes the system,
what already exists, the full source catalogue, the recommended web build, and —
most importantly — the rules that must never be broken. Everything here is for a
**consenting, identity-verified client and their consenting family**, reading
**lawful public/semi-public records about *them***, using the **client's own
data**.

---

## 0. READ THIS FIRST — the rules that cannot be broken

These are not optional. They are what makes the product lawful and defensible to
a client, their counsel, a regulator, and a court. They must be enforced **in the
backend code**, not just in the UI.

1. **Consent-gated.** Nothing is queried unless the subject is a verified client
   or their consenting family, or an entity/asset/identifier/counterparty the
   client declared as their own. Reject any query whose subject is not in scope.
2. **Lawful, allowlisted sources only.** Only sources on the catalogue (Section
   5), and only where the source's terms permit automated collection.
3. **No surveillance or profiling of third parties.**
4. **No non-public, stolen, or leaked third-party data.** Breach/leak checks
   accept **only the client's own declared identifiers**, via a licensed
   provider. Never ingest a raw leaked database.
5. **No fabricated outputs.** A source that returns nothing is recorded as an
   absence, never inferred as a presence.

**There must be no API endpoint that accepts an arbitrary third-party target.**
The entire system is seeded from the client's own declared data. If a proposed
feature cannot run inside these five rules, do not build it.

What this is: a personal/family **"what can an adversary lawfully find out about
me, and how do I reduce it"** service. What this is **not**: a way to locate or
profile other people's wealth. The second thing is illegal and is explicitly out
of scope.

---

## 1. What already exists (the engine)

A Python package, `wealth_exposure/`, implements the gated pipeline. The web app
should **call this engine server-side**, not reimplement collection in the
browser. Module map:

| Module | Role |
| --- | --- |
| `guardrails.py` | The five hard constraints, as code. Every path routes through here. |
| `consent.py` | `ConsentScope` — the source of truth for who/what may be queried; owner attribution. |
| `allowlist.py` | The 88-source catalogue + per-source automation/rate-limit policy. |
| `collectors/base.py` | `Collector` base — enforces gate + allowlist + rate limit before any fetch. |
| `collectors/companies_house.py` | Client's own UK company filings. |
| `collectors/breach_exposure.py` | Client's own identifiers only, via licensed provider. |
| `collectors/sanctions_screening.py` | Client's own sanctions/PEP status. |
| `collectors/register.py` | **Generic** collector for any allowlisted source via an adapter. |
| `counterparty.py` | Firm-level due diligence on firms the client holds assets with (declared counterparties). |
| `resolver.py` | Cross-referencing: name variants, address correlation, network mapping, two-source rule. |
| `inference/regulatory_scope.py` | Probability a *firm* is in a published rule's scope (labelled "unconfirmed by firm"). |
| `watchers/` | Foresight watchers (register changes, counterparty filings, sanctions updates) + runner. |
| `registry.py` | Builds collectors for every automatable source from injected adapters. |
| `orchestrator.py` | `ExposureRun` — one call sweeps all of a client's own subjects. |
| `exposure_register.py` | Per-client living record of exposures + status. |

Run it: `python -m pytest` (45 tests) and `python examples/demo.py` (no-network
demo with stub data).

---

## 2. Recommended web architecture

A thin client over a gated backend. Suggested shape (technology is the dev's
choice; these are recommendations):

```
[ Client portal (web) ]
        |  HTTPS, authenticated
        v
[ Backend API (e.g. FastAPI/Node) ]
   - AuthN/AuthZ (per-client isolation)
   - Identity verification (KYC) integration
   - Consent service  ──────────────► Consent store (DB)
   - Job queue ──► Collector workers ──► wealth_exposure engine
                                          (collectors / counterparty / resolver)
   - Scheduler ──► Watchers (periodic)
        |
        v
[ Exposure register store (DB) ]  ──►  Dashboard, alerts, reports
[ Secrets manager ]  (source API keys)
```

Principles:
- **All collection is server-side**, behind the consent gate. The browser never
  calls a source directly and never holds source API keys.
- **One worker per source type**, wrapping the existing collectors. Use
  `RegisterCollector` + a per-source adapter so adding a country is configuration.
- **Watchers run on a schedule** (e.g. nightly) and write flags to the register.
- **Every client's data is isolated**; one client can never see another's.

Recommended stack (optional): Python **FastAPI** wrapping `wealth_exposure/`,
**PostgreSQL** for consent + exposure register, **Celery/RQ** for workers and a
beat scheduler for watchers, a **secrets manager/KMS** for API keys, **React/Next**
for the portal.

---

## 3. Consent & identity verification (the mandatory gate)

- Integrate a **KYC/identity-verification provider**; a client is only
  `verified=True` after it passes. Family members are each verified separately.
- Capture and store a **consent scope per client**: which entities, assets,
  identifiers, and counterparties they declare as their own, with timestamps and
  the ability to **revoke**.
- Every collection call checks the scope (the existing `ConsentScope.covers`).
- Keep an **immutable audit log** of every query: subject, source, time, result.
  This is the evidence that the service stayed lawful.

---

## 4. Security & data protection (this handles personal data)

This processes personal data, so data-protection law applies (UK GDPR / GDPR and
local equivalents). Recommended before launch:

- **Lawful basis = explicit consent**; record it; honour erasure/rectification.
- **Data minimisation & retention limits**; delete on request and on schedule.
- **Encryption** at rest and in transit; **least-privilege** access; secrets in a
  vault/KMS, never in code or the client.
- **DPIA** (data-protection impact assessment) and an independent **legal review**
  of scope and sources before go-live.
- **Respect each source's terms and rate limits** — `terms_permit_automation` in
  the catalogue marks which may be automated; the rest need manual/licensed
  handling. Public availability is not permission to bulk-collect.
- Logging, monitoring, and a security review/pen-test.

---

## 5. The source catalogue (the list)

**88 sources — 57 automatable (official API / bulk feed), 31 manual** (paid,
access-restricted, or terms unclear → integrate by hand under the source's terms;
do not scrape). `Collect = API/auto` means an adapter can be built now;
`Collect = manual` means a human process under that source's terms.

To add a source: append a `Source(...)` to `wealth_exposure/allowlist.py` and
provide an adapter; the collector, gate, and rate-limit handling come for free.

| Source ID | Name | Jurisdiction | Category | Collect |
| --- | --- | --- | --- | --- |
| `adverse_media_licensed` | Licensed adverse-media screening | GLOBAL | adverse_media | API/auto |
| `breach_licensed_provider` | Licensed breach-exposure provider | GLOBAL | breach_licensed | API/auto |
| `certificate_transparency` | Certificate Transparency logs | GLOBAL | certificate_transparency | API/auto |
| `domain_rdap_whois` | RDAP / WHOIS domain registration | GLOBAL | domain | API/auto |
| `data_broker_optout` | Data-broker / people-search (own footprint) | GLOBAL | footprint | manual |
| `bo_access_monitor` | Beneficial-ownership register access monitor | GLOBAL | foresight | manual |
| `fatf_statements` | FATF public statements and lists | GLOBAL | foresight | API/auto |
| `regulator_publications` | Regulator publications / consultations feed | GLOBAL | foresight | API/auto |
| `treaty_exchange_monitor` | Tax-treaty / information-exchange monitor | GLOBAL | foresight | manual |
| `pep_licensed_list` | Licensed PEP screening list | GLOBAL | pep | API/auto |
| `un_sc_sanctions` | UN Security Council consolidated list | GLOBAL | sanctions | API/auto |
| `equasis_vessels` | Equasis vessel information | GLOBAL | vessel | API/auto |
| `imo_gisis` | IMO GISIS ship data | GLOBAL | vessel | manual |
| `eu_esma_registers` | ESMA registers | EU | regulator | API/auto |
| `eu_consolidated_sanctions` | EU consolidated sanctions list | EU | sanctions | API/auto |
| `uk_caa_ginfo` | CAA G-INFO aircraft register | UK | aircraft | API/auto |
| `uk_register_overseas_entities` | Register of Overseas Entities | UK | beneficial_ownership | API/auto |
| `uk_charity_commission` | Charity Commission (E&W) | UK | charity | API/auto |
| `uk_ccni` | Charity Commission for Northern Ireland | UK | charity | manual |
| `uk_oscr` | OSCR (Scottish charities) | UK | charity | API/auto |
| `uk_companies_house` | Companies House | UK | corporate | API/auto |
| `uk_find_case_law` | Find Case Law (The National Archives) | UK | court | API/auto |
| `uk_gazette` | The Gazette | UK | gazette | API/auto |
| `uk_insolvency_register` | Insolvency Register (England & Wales) | UK | insolvency | API/auto |
| `uk_ipo_designs` | UK IPO Designs | UK | ip | API/auto |
| `uk_ipo_patents` | UK IPO Patents (Ipsum) | UK | ip | API/auto |
| `uk_ipo_trademarks` | UK IPO Trade Marks | UK | ip | API/auto |
| `uk_fca_nsm` | FCA National Storage Mechanism (TR-1 etc.) | UK | markets | API/auto |
| `uk_lse_rns` | London Stock Exchange RNS | UK | markets | manual |
| `uk_land_registry_price_paid` | HM Land Registry Price Paid Data | UK | property | API/auto |
| `uk_land_registry_title` | HM Land Registry Title Register | UK | property | manual |
| `uk_lps_ni` | Land & Property Services NI | UK | property | manual |
| `uk_registers_scotland` | Registers of Scotland | UK | property | manual |
| `uk_land_registry_alert` | HM Land Registry Property Alert | UK | property_alert | manual |
| `uk_fca_register` | FCA Register | UK | regulator | API/auto |
| `ofsi_sanctions` | UK OFSI consolidated list | UK | sanctions | API/auto |
| `us_faa_registry` | FAA aircraft registry | US | aircraft | API/auto |
| `us_irs_990` | IRS Form 990 (nonprofits) | US | charity | API/auto |
| `us_ca_sos` | California Secretary of State | US | corporate | API/auto |
| `us_de_sos` | Delaware Division of Corporations | US | corporate | manual |
| `us_ny_sos` | New York Department of State | US | corporate | API/auto |
| `us_wy_sos` | Wyoming Secretary of State | US | corporate | API/auto |
| `us_courtlistener` | CourtListener / RECAP | US | court | API/auto |
| `us_pacer` | PACER federal courts | US | court | manual |
| `us_uspto_patents` | USPTO Patents (PatentsView) | US | ip | API/auto |
| `us_uspto_trademarks` | USPTO Trademarks (TSDR) | US | ip | API/auto |
| `us_sec_13d_13g` | SEC 13D / 13G beneficial ownership | US | markets | API/auto |
| `us_sec_edgar` | SEC EDGAR | US | markets | API/auto |
| `us_sec_forms345` | SEC Forms 3/4/5 (insider) | US | markets | API/auto |
| `us_county_recorders` | County recorder property records (varies) | US | property | manual |
| `ofac_sdn` | US OFAC SDN list | US | sanctions | API/auto |
| `ofac_consolidated` | US OFAC consolidated (non-SDN) | US | sanctions | API/auto |
| `ae_adgm` | ADGM Registration Authority | AE | corporate | manual |
| `ae_difc` | DIFC Registrar of Companies | AE | corporate | manual |
| `ae_dld` | Dubai Land Department (transaction data) | AE | property | manual |
| `bh_sijilat` | Bahrain Sijilat commercial register | BH | corporate | manual |
| `bm_roc` | Bermuda Registrar of Companies | BM | corporate | manual |
| `br_jucesp` | Brazil Junta Comercial (state registries) | BR | corporate | manual |
| `bs_registrar` | Bahamas Registrar General | BS | corporate | manual |
| `ch_zefix` | Switzerland Zefix commercial register | CH | corporate | API/auto |
| `ch_sogc` | Swiss Official Gazette of Commerce (SOGC) | CH | gazette | API/auto |
| `ch_finma` | FINMA register | CH | regulator | API/auto |
| `cy_registrar` | Cyprus Registrar of Companies | CY | corporate | API/auto |
| `de_unternehmensregister` | Germany Unternehmensregister / Handelsregister | DE | corporate | manual |
| `es_rmc` | Spain Registro Mercantil Central | ES | corporate | manual |
| `fr_inpi_rne` | France INPI Registre National des Entreprises | FR | corporate | API/auto |
| `hk_icris` | Hong Kong Companies Registry (ICRIS) | HK | corporate | manual |
| `hk_hkex` | HKEX disclosure of interests | HK | markets | API/auto |
| `hk_sfc` | Hong Kong SFC register | HK | regulator | API/auto |
| `ie_cro` | Ireland Companies Registration Office | IE | corporate | manual |
| `in_mca21` | India MCA21 company register | IN | corporate | manual |
| `it_registro_imprese` | Italy Registro Imprese | IT | corporate | manual |
| `jp_corporate_number` | Japan NTA Corporate Number system | JP | corporate | API/auto |
| `jp_edinet` | Japan EDINET (securities filings) | JP | markets | API/auto |
| `ky_general_registry` | Cayman Islands General Registry | KY | corporate | manual |
| `li_hr` | Liechtenstein commercial register | LI | corporate | manual |
| `lu_rbe` | Luxembourg RBE (legitimate interest) | LU | beneficial_ownership | manual |
| `lu_rcs` | Luxembourg RCS | LU | corporate | API/auto |
| `lu_luxse` | Luxembourg Stock Exchange | LU | markets | API/auto |
| `mt_mbr` | Malta Business Registry | MT | corporate | API/auto |
| `nl_kvk` | Netherlands KvK | NL | corporate | API/auto |
| `pa_registro_publico` | Panama Public Registry | PA | corporate | API/auto |
| `pa_gaceta` | Panama Gaceta Oficial | PA | gazette | API/auto |
| `qa_qfc` | Qatar Financial Centre register | QA | corporate | manual |
| `sg_acra_bizfile` | Singapore ACRA BizFile | SG | corporate | manual |
| `sg_ipos` | Singapore IPOS (IP) | SG | ip | API/auto |
| `sg_sgx` | Singapore Exchange disclosures | SG | markets | API/auto |
| `sg_mas_fid` | Singapore MAS Financial Institutions Directory | SG | regulator | API/auto |

*All `Collect` flags are conservative defaults — re-verify each source's current
terms of use before integrating.*

---

## 6. Recommended build order (integrations first)

Start with automatable, official-API sources anchored to the client's own data:

1. **Companies House** (`uk_companies_house`) — client's own UK entities.
2. **Own-credential breach check** (`breach_licensed_provider`) — licensed
   provider, **own identifiers only**.
3. **Sanctions/PEP screening** (`ofac_sdn`, `ofsi_sanctions`,
   `eu_consolidated_sanctions`, `un_sc_sanctions`) — client's own status.
4. **SEC EDGAR** (`us_sec_edgar`) — US filings on the client's own entities.
5. **FCA Register** (`uk_fca_register`) — regulatory status of the client's own
   counterparties.
6. **Data-broker removal** (`data_broker_optout`) — client's own footprint, via a
   privacy provider.

Each: build an adapter implementing `fetch(identifier) -> list[dict]`, register it
in `CollectorRegistry`, store API keys in the secrets manager, honour rate limits.

---

## 7. Recommended features to add (the "recommended things")

- **Identity-verification flow** and **consent-management UI** (capture scope,
  per-family-member, revoke).
- **Client dashboard**: the exposure register with status (open / reducing /
  resolved / monitoring).
- **Reduction workflows**: data-broker opt-out tracking, register suppression
  where permitted, impersonation/look-alike-domain takedown.
- **Alerting**: email/SMS/push when a watcher finds a new exposure.
- **Counterparty-risk view**: firms the client holds assets with, with
  early-warning flags (qualified/adverse audit opinion, enforcement, sanctions).
- **Reports**: an exportable "adversary's-eye view" for the client and their
  counsel.
- **Scheduler** for the watchers (register changes, sanctions updates,
  counterparty filings).
- **Source-governance admin**: API keys, per-source rate-limit settings, and the
  manual-vs-automatable status from the catalogue.

---

## 8. What NOT to build (hard nos)

- No endpoint that accepts an **arbitrary third-party target**.
- No **"find where wealth is held"** / mass lookup over people who have not
  consented.
- No ingesting **leaked/breached databases** for discovery — breach checks are
  the subject's **own identifiers only**, via a licensed provider.
- No **scraping against a source's terms** — honour the `manual` flag.
- No **profiling of non-consenting people**, and counterparty due diligence stays
  **firm-level** (a firm's public regulatory/financial status), never a route to
  its owners, customers, or any person's wealth.

---

## 9. Quick reference

- Repo branch: `claude/blissful-galileo-2TXLI`
- Read first: `wealth_exposure/guardrails.py`, `consent.py`, `allowlist.py`,
  `orchestrator.py`, then `README.md` and `CLAUDE.md`.
- Verify: `python -m pytest` (45 tests) · `python examples/demo.py`.
