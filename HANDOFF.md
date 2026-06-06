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

---

## Appendix A — Counterparty venue & custody reference

This appendix is a **counterparty-risk reference**: the categories of venue and
custodian where a client's *own* value tends to sit, so the firm can assess
**the client's** counterparty risk ("is my money safe here?"). It is **not** a
directory for locating anyone else's holdings, and it is **not** a source
allowlist. For who is actually registered/authorised in any country, the
regulator register (Section 5) is the source of truth. All status is **[verify]**
— venues are acquired, licensed, and de-licensed constantly.

### A.1 Custody providers by asset class
- **Precious metals / bullion:** Brink's, Loomis, Malca-Amit; LBMA-approved bank and refinery vaults
- **Diamonds / gems / jewellery:** Malca-Amit, Brink's; secure facilities at the Antwerp, Dubai and Ramat Gan exchanges; freeport storage
- **Fine art:** Freeports — Geneva, Le Freeport Luxembourg, Le Freeport Singapore, Delaware; specialists — Crozier/Iron Mountain, UOVO, Gander & White, Cadogan Tate, Momart
- **Listed securities / funds:** Global custodian banks — BNY, State Street, JPMorgan, Citi, Northern Trust, BNP Paribas Securities Services, HSBC; private banks — UBS, Julius Baer, Pictet, Lombard Odier
- **Cash / deposits:** the private banks above and the private-bank arms of universal banks
- **Cryptoassets:** Qualified custodians — Coinbase Custody, BitGo, Fireblocks, Anchorage, Fidelity Digital Assets, Komainu, Copper; self-custody hardware — Ledger, Trezor
- **Aircraft / yachts:** Management firms — NetJets, VistaJet, Jet Aviation; Fraser, Burgess, Edmiston — plus the flag registries in Section 5

### A.2 Commodity exchanges
- **North America:** CME Group (CME, CBOT, NYMEX, COMEX); Intercontinental Exchange (ICE, ICE Futures US); Minneapolis Grain Exchange. Regulator: CFTC
- **Europe:** London Metal Exchange; ICE Futures Europe (UK, FCA); European Energy Exchange (Germany); Euronext; ICE Endex
- **Asia:** Shanghai Futures Exchange, Shanghai International Energy Exchange, Dalian Commodity Exchange, Zhengzhou Commodity Exchange (China); MCX, NCDEX (India); Japan Exchange Group / Osaka (absorbed TOCOM); SGX (Singapore); Bursa Malaysia Derivatives
- **Middle East & other:** Dubai Gold & Commodities Exchange; Gulf Mercantile Exchange (formerly DME); Moscow Exchange; B3 (Brazil); JSE commodity derivatives (South Africa); ASX commodities (Australia)

### A.3 Crypto exchanges (home jurisdiction; status [verify])
- **Global majors:** Binance (multiple settlements, no single historical HQ); Coinbase (US, listed); Kraken (US); OKX (Seychelles); Bybit (UAE); Bitget (Seychelles/Singapore); KuCoin (Seychelles); Gate (Cayman/various); HTX, formerly Huobi (Seychelles); Crypto.com (Singapore); MEXC (Seychelles)
- **Regulated / regional anchors:** Gemini (US, NYDFS trust); Bitstamp (Luxembourg/EU); Bitfinex (BVI/iFinex); Bitvavo (Netherlands); WhiteBIT (Europe); Upbit, Bithumb, Coinone (South Korea); bitFlyer (Japan); Bitso (Mexico); Luno (UK/South Africa); CoinDCX (India); Indodax (Indonesia); Independent Reserve (Australia)
- **Derivatives-led:** Bybit, OKX; Deribit (options); BingX; Phemex
- **Decentralised (non-custodial):** Uniswap, PancakeSwap, Curve, SushiSwap, Balancer, dYdX, Hyperliquid, GMX, Aerodrome; Raydium and Jupiter on Solana

### A.4 Regional platforms (neobanks / payments / crypto)
- **United Kingdom:** Monzo, Starling, Revolut, Chase UK, Kroo; crypto (FCA-registered) Coinbase, Kraken, Bitstamp, Gemini
- **Europe (EU/EEA):** N26, bunq, Bitpanda, Vivid, Qonto (business), Lydia, Tomorrow; crypto Bitvavo, WhiteBIT, Bitpanda, Bitstamp
- **United States:** Chime, Varo, Current, SoFi, Cash App; business Mercury, Brex; crypto Coinbase, Kraken, Gemini
- **Latin America:** Nubank, Ualá, Mercado Pago, C6 Bank, Inter, RappiPay; crypto Bitso, Mercado Bitcoin, Ripio, Lemon, Buenbit
- **Asia:** WeBank, MyBank (China), KakaoBank, Toss (Korea), PayPay (Japan), GXS, Trust Bank (Singapore), Tonik (Philippines), Paytm Payments Bank (India); crypto Upbit, Bithumb, Coinone (Korea), bitFlyer, Coincheck, bitbank (Japan), CoinDCX (India), Indodax (Indonesia), Bitkub (Thailand), Coins.ph (Philippines)
- **Middle East:** Liv, Wio (UAE), Mashreq Neo; crypto Bybit, BitOasis, Rain, CoinMENA (UAE & Bahrain)
- **Africa:** Kuda, OPay, Carbon (Nigeria), TymeBank (South Africa); crypto Luno, VALR, Yellow Card
- **Global multi-currency / e-money / payments:** Wise, Revolut, Payoneer, Airwallex, PayPal, Stripe, Adyen, Checkout.com, Block (Square)

---

## Appendix B — Major institutions by jurisdiction (working reference, not exhaustive)

These are **major, publicly-known** institutions only. This is not, and cannot
be, a list of *all companies* in a jurisdiction — each register holds hundreds of
thousands to millions of entities, and the **register is the authoritative
complete source** (queried at runtime against the client's own declared
holdings). Status is **[verify]**.

### United Kingdom
- **Banks:** Barclays, HSBC UK, Lloyds (Halifax, Bank of Scotland), NatWest (RBS, Ulster), Santander UK, Standard Chartered, Nationwide, TSB, Co-operative Bank, Metro Bank, Virgin Money
- **Private banks / wealth:** Coutts, C. Hoare & Co, Rothschild & Co, Cazenove/Schroders, St James's Place, Rathbones, RBC Brewin Dolphin, Brooks Macdonald, Quilter, Investec Wealth
- **Platforms:** Hargreaves Lansdown, AJ Bell, interactive investor
- **Exchanges:** London Stock Exchange (LSEG), LME, ICE Futures Europe, Aquis
- **Crypto (FCA-registered):** Coinbase, Kraken, Bitstamp, Gemini, Komainu, Copper, Archax, CEX.IO
- **Neobanks / fintech / payments:** Monzo, Starling, Revolut, Chase UK, Kroo, Wise, Curve, Tide, Allica, Atom, Monese

### United States
- **Banks:** JPMorgan Chase, Bank of America, Citi, Wells Fargo, U.S. Bancorp, PNC, Truist, Goldman Sachs, Morgan Stanley, Capital One
- **Wealth / brokerage / asset mgmt:** Fidelity, Charles Schwab, Vanguard, BlackRock, Merrill, Morgan Stanley/E*Trade, Edward Jones, Raymond James, Northern Trust, BNY/Pershing, State Street
- **Exchanges:** NYSE, Nasdaq, CME Group, ICE, Cboe
- **Crypto:** Coinbase, Kraken, Gemini, BitGo, Anchorage, Fidelity Digital Assets, Paxos, Circle
- **Fintech / neobank / payments:** Chime, Varo, SoFi, Current, Cash App (Block), PayPal, Stripe, Mercury, Brex, Ramp

### Switzerland
UBS (incl. Credit Suisse), Julius Baer, Pictet, Lombard Odier, Vontobel, J. Safra Sarasin, EFG International, UBP, Zürcher Kantonalbank, PostFinance, Raiffeisen · **Exchange:** SIX · **Crypto:** Sygnum, AMINA (ex-SEBA), Bitcoin Suisse

### Germany
Deutsche Bank, Commerzbank, DZ Bank, KfW, Berenberg, Hauck Aufhäuser, LBBW, BayernLB · **Fintech:** N26, Trade Republic, Solaris, Vivid · **Exchange:** Deutsche Börse, EEX · **Crypto:** Boerse Stuttgart Digital, Bitpanda

### France
BNP Paribas, Crédit Agricole, Société Générale, BPCE (Natixis), Crédit Mutuel, La Banque Postale; Edmond de Rothschild, Oddo BHF · **Exchange:** Euronext Paris · **Fintech:** Qonto, Lydia, Shine

### Rest of Europe
- **Netherlands:** ABN AMRO, ING, Rabobank, Van Lanschot Kempen; bunq, Bitvavo, Adyen; Euronext Amsterdam
- **Ireland:** Bank of Ireland, AIB, PTSB
- **Spain:** Santander, BBVA, CaixaBank, Sabadell, Bankinter; BME
- **Italy:** Intesa Sanpaolo, UniCredit, Banco BPM, Mediobanca, FinecoBank; Borsa Italiana
- **Luxembourg:** Banque de Luxembourg, BIL, Quintet; Bitstamp; Luxembourg Stock Exchange
- **Liechtenstein:** LGT, VP Bank, LLB
- **Cyprus:** Bank of Cyprus, Hellenic Bank
- **Malta:** Bank of Valletta, HSBC Malta

### Middle East
- **UAE:** Emirates NBD, First Abu Dhabi Bank, ADCB, Mashreq, Dubai Islamic Bank; Liv, Wio; Bybit, BitOasis, Rain, M2, CoinMENA; DFM, ADX, Nasdaq Dubai
- **Qatar:** QNB, Commercial Bank, Doha Bank; Qatar Stock Exchange
- **Bahrain:** Bank ABC, Gulf International Bank; Rain, CoinMENA

### Asia
- **Singapore:** DBS, OCBC, UOB, Bank of Singapore; GXS, Trust Bank, MariBank; SGX; Independent Reserve, Crypto.com, Sygnum
- **Hong Kong:** HSBC, Hang Seng, Standard Chartered HK, BOC (HK); HKEX; HashKey, OSL
- **Japan:** MUFG, SMBC, Mizuho, Japan Post Bank, Nomura, Daiwa; PayPay, Rakuten Bank; bitFlyer, Coincheck, bitbank; JPX
- **South Korea:** KB Kookmin, Shinhan, Hana, Woori; KakaoBank, Toss Bank, K Bank; Upbit, Bithumb, Coinone; KRX
- **India:** SBI, HDFC, ICICI, Axis, Kotak; Paytm, PhonePe; NSE, BSE; CoinDCX, WazirX

### Latin America
- **Brazil:** Itaú Unibanco, Bradesco, Banco do Brasil, Santander Brasil, BTG Pactual, Nubank, C6, Inter; B3; Mercado Bitcoin, Bitso
- **Mexico:** BBVA México, Banorte, Santander México, Citibanamex; Nu, Mercado Pago; Bitso
- **Argentina:** Banco Galicia, Santander, BBVA; Ualá, Lemon, Belo, Buenbit, Ripio

### Africa
- **Nigeria:** GTBank, Zenith, Access, UBA, First Bank; Kuda, OPay, Carbon; Yellow Card, Quidax
- **South Africa:** Standard Bank, FirstRand/FNB, Absa, Nedbank, Investec; TymeBank, Discovery Bank; JSE; Luno, VALR
- **Kenya:** Equity Bank, KCB, Safaricom M-Pesa

### Offshore / trust centres
- **Cayman:** Butterfield, Cayman National, fund admins/trust companies; CSX
- **Bermuda:** Butterfield, Clarien, HSBC Bermuda; BMA-regulated (re)insurers; BSX
- **Bahamas:** private banks & trust companies; BISX
- **Panama:** Banco General, Banistmo, Multibank; Panama Stock Exchange
- **Jersey / Guernsey:** RBC, Butterfield, Barclays; trust companies

### Global (cross-border)
- **Custodian banks:** BNY, State Street, JPMorgan, Citi, Northern Trust, BNP Paribas SS, HSBC, BBH, RBC Investor Services, CACEIS, SGSS
- **Asset managers:** BlackRock, Vanguard, Fidelity, State Street/SSGA, Amundi, UBS AM, PIMCO, Capital Group, JPMorgan AM
- **Payments / e-money / multi-currency:** Wise, Revolut, Payoneer, Airwallex, PayPal, Stripe, Adyen, Checkout.com, Block (Square), Nium, Rapyd

> Reminder: this whole appendix is a **category-level counterparty reference**
> anchored to the client's own holdings. It is not a list of who holds what, and
> the system never uses it to look up a non-client. The authoritative, current,
> complete set of firms in any jurisdiction is that jurisdiction's regulator/
> company register (Section 5), queried at runtime under its terms of use.
