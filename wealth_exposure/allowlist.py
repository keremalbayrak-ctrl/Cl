"""Lawful source allowlist — the catalogue of official/licensed sources the
system may read ABOUT THE CLIENT.

Adding a source here does NOT weaken any guardrail: every collection still
passes through the consent gate, so a larger catalogue only means more lawful
public records can be read about the consenting client/family — never about a
non-client. Collectors are built per source over time; this is the registry of
what is permitted, organised by jurisdiction and category.

`terms_permit_automation` is a conservative per-source judgement. Where a source
is paid, access-restricted, or its terms are unclear, it is set False so the base
collector refuses automated collection until a human integrates it under the
source's actual terms (public availability != permission to bulk-collect). All
flags are [verify] against each source's current terms of use.
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

    __contains__ = contains

    def get(self, source_id) -> Source:
        return self._by_id[source_id]

    def all(self):
        return list(self._by_id.values())

    def ids(self):
        return sorted(self._by_id)

    def by_jurisdiction(self, jurisdiction):
        return [s for s in self._by_id.values() if s.jurisdiction == jurisdiction]

    def by_category(self, category):
        return [s for s in self._by_id.values() if s.category == category]

    def automatable(self):
        return [s for s in self._by_id.values() if s.terms_permit_automation]

    def __len__(self):
        return len(self._by_id)


# --- Cross-jurisdiction: sanctions / PEP -----------------------------------
_SANCTIONS = [
    Source("ofsi_sanctions", "UK OFSI consolidated list", "UK", "sanctions", True, 60),
    Source("ofac_sdn", "US OFAC SDN list", "US", "sanctions", True, 60),
    Source("ofac_consolidated", "US OFAC consolidated (non-SDN)", "US", "sanctions", True, 60),
    Source("eu_consolidated_sanctions", "EU consolidated sanctions list", "EU", "sanctions", True, 60),
    Source("un_sc_sanctions", "UN Security Council consolidated list", "GLOBAL", "sanctions", True, 60),
    Source("pep_licensed_list", "Licensed PEP screening list", "GLOBAL", "pep", True, 60),
]

# --- Cross-jurisdiction: foresight feeds -----------------------------------
_FORESIGHT = [
    Source("fatf_statements", "FATF public statements and lists", "GLOBAL", "foresight", True, 30),
    Source("regulator_publications", "Regulator publications / consultations feed", "GLOBAL", "foresight", True, 60),
    Source("treaty_exchange_monitor", "Tax-treaty / information-exchange monitor", "GLOBAL", "foresight", False, 30),
    Source("bo_access_monitor", "Beneficial-ownership register access monitor", "GLOBAL", "foresight", False, 30),
]

# --- Footprint / breach / domain (client's own data) -----------------------
_FOOTPRINT = [
    Source("breach_licensed_provider", "Licensed breach-exposure provider", "GLOBAL", "breach_licensed", True, 60),
    Source("adverse_media_licensed", "Licensed adverse-media screening", "GLOBAL", "adverse_media", True, 60),
    Source("certificate_transparency", "Certificate Transparency logs", "GLOBAL", "certificate_transparency", True, 120),
    Source("domain_rdap_whois", "RDAP / WHOIS domain registration", "GLOBAL", "domain", True, 120),
    Source("data_broker_optout", "Data-broker / people-search (own footprint)", "GLOBAL", "footprint", False, 30),
]

# --- United Kingdom --------------------------------------------------------
_UK = [
    Source("uk_companies_house", "Companies House", "UK", "corporate", True, 600),
    Source("uk_register_overseas_entities", "Register of Overseas Entities", "UK", "beneficial_ownership", True, 120),
    Source("uk_land_registry_price_paid", "HM Land Registry Price Paid Data", "UK", "property", True, 120),
    Source("uk_land_registry_title", "HM Land Registry Title Register", "UK", "property", False, 30),
    Source("uk_land_registry_alert", "HM Land Registry Property Alert", "UK", "property_alert", False, 30),
    Source("uk_registers_scotland", "Registers of Scotland", "UK", "property", False, 30),
    Source("uk_lps_ni", "Land & Property Services NI", "UK", "property", False, 30),
    Source("uk_fca_register", "FCA Register", "UK", "regulator", True, 120),
    Source("uk_fca_nsm", "FCA National Storage Mechanism (TR-1 etc.)", "UK", "markets", True, 60),
    Source("uk_lse_rns", "London Stock Exchange RNS", "UK", "markets", False, 60),
    Source("uk_insolvency_register", "Insolvency Register (England & Wales)", "UK", "insolvency", True, 60),
    Source("uk_gazette", "The Gazette", "UK", "gazette", True, 120),
    Source("uk_find_case_law", "Find Case Law (The National Archives)", "UK", "court", True, 60),
    Source("uk_ipo_patents", "UK IPO Patents (Ipsum)", "UK", "ip", True, 60),
    Source("uk_ipo_trademarks", "UK IPO Trade Marks", "UK", "ip", True, 60),
    Source("uk_ipo_designs", "UK IPO Designs", "UK", "ip", True, 60),
    Source("uk_charity_commission", "Charity Commission (E&W)", "UK", "charity", True, 120),
    Source("uk_oscr", "OSCR (Scottish charities)", "UK", "charity", True, 60),
    Source("uk_ccni", "Charity Commission for Northern Ireland", "UK", "charity", False, 30),
    Source("uk_caa_ginfo", "CAA G-INFO aircraft register", "UK", "aircraft", True, 60),
]

# --- United States ---------------------------------------------------------
_US = [
    Source("us_sec_edgar", "SEC EDGAR", "US", "markets", True, 600),
    Source("us_sec_forms345", "SEC Forms 3/4/5 (insider)", "US", "markets", True, 600),
    Source("us_sec_13d_13g", "SEC 13D / 13G beneficial ownership", "US", "markets", True, 600),
    Source("us_de_sos", "Delaware Division of Corporations", "US", "corporate", False, 30),
    Source("us_ny_sos", "New York Department of State", "US", "corporate", True, 60),
    Source("us_ca_sos", "California Secretary of State", "US", "corporate", True, 60),
    Source("us_wy_sos", "Wyoming Secretary of State", "US", "corporate", True, 60),
    Source("us_county_recorders", "County recorder property records (varies)", "US", "property", False, 30),
    Source("us_pacer", "PACER federal courts", "US", "court", False, 30),
    Source("us_courtlistener", "CourtListener / RECAP", "US", "court", True, 60),
    Source("us_uspto_patents", "USPTO Patents (PatentsView)", "US", "ip", True, 120),
    Source("us_uspto_trademarks", "USPTO Trademarks (TSDR)", "US", "ip", True, 60),
    Source("us_irs_990", "IRS Form 990 (nonprofits)", "US", "charity", True, 120),
    Source("us_faa_registry", "FAA aircraft registry", "US", "aircraft", True, 60),
]

# --- Europe (ex-UK) --------------------------------------------------------
_EU = [
    Source("eu_esma_registers", "ESMA registers", "EU", "regulator", True, 60),
    Source("ie_cro", "Ireland Companies Registration Office", "IE", "corporate", False, 30),
    Source("de_unternehmensregister", "Germany Unternehmensregister / Handelsregister", "DE", "corporate", False, 30),
    Source("fr_inpi_rne", "France INPI Registre National des Entreprises", "FR", "corporate", True, 60),
    Source("nl_kvk", "Netherlands KvK", "NL", "corporate", True, 60),
    Source("es_rmc", "Spain Registro Mercantil Central", "ES", "corporate", False, 30),
    Source("it_registro_imprese", "Italy Registro Imprese", "IT", "corporate", False, 30),
    Source("lu_rcs", "Luxembourg RCS", "LU", "corporate", True, 60),
    Source("lu_rbe", "Luxembourg RBE (legitimate interest)", "LU", "beneficial_ownership", False, 30),
    Source("lu_luxse", "Luxembourg Stock Exchange", "LU", "markets", True, 60),
    Source("ch_zefix", "Switzerland Zefix commercial register", "CH", "corporate", True, 60),
    Source("ch_sogc", "Swiss Official Gazette of Commerce (SOGC)", "CH", "gazette", True, 60),
    Source("ch_finma", "FINMA register", "CH", "regulator", True, 60),
    Source("li_hr", "Liechtenstein commercial register", "LI", "corporate", False, 30),
    Source("cy_registrar", "Cyprus Registrar of Companies", "CY", "corporate", True, 60),
    Source("mt_mbr", "Malta Business Registry", "MT", "corporate", True, 60),
]

# --- Asia ------------------------------------------------------------------
_ASIA = [
    Source("sg_acra_bizfile", "Singapore ACRA BizFile", "SG", "corporate", False, 30),
    Source("sg_mas_fid", "Singapore MAS Financial Institutions Directory", "SG", "regulator", True, 60),
    Source("sg_sgx", "Singapore Exchange disclosures", "SG", "markets", True, 60),
    Source("sg_ipos", "Singapore IPOS (IP)", "SG", "ip", True, 60),
    Source("hk_icris", "Hong Kong Companies Registry (ICRIS)", "HK", "corporate", False, 30),
    Source("hk_sfc", "Hong Kong SFC register", "HK", "regulator", True, 60),
    Source("hk_hkex", "HKEX disclosure of interests", "HK", "markets", True, 60),
    Source("jp_corporate_number", "Japan NTA Corporate Number system", "JP", "corporate", True, 60),
    Source("jp_edinet", "Japan EDINET (securities filings)", "JP", "markets", True, 60),
    Source("in_mca21", "India MCA21 company register", "IN", "corporate", False, 30),
]

# --- Middle East -----------------------------------------------------------
_ME = [
    Source("ae_difc", "DIFC Registrar of Companies", "AE", "corporate", False, 30),
    Source("ae_adgm", "ADGM Registration Authority", "AE", "corporate", False, 30),
    Source("ae_dld", "Dubai Land Department (transaction data)", "AE", "property", False, 30),
    Source("qa_qfc", "Qatar Financial Centre register", "QA", "corporate", False, 30),
    Source("bh_sijilat", "Bahrain Sijilat commercial register", "BH", "corporate", False, 30),
]

# --- Offshore / Latin America ----------------------------------------------
_OFFSHORE = [
    Source("ky_general_registry", "Cayman Islands General Registry", "KY", "corporate", False, 30),
    Source("bm_roc", "Bermuda Registrar of Companies", "BM", "corporate", False, 30),
    Source("bs_registrar", "Bahamas Registrar General", "BS", "corporate", False, 30),
    Source("pa_registro_publico", "Panama Public Registry", "PA", "corporate", True, 60),
    Source("pa_gaceta", "Panama Gaceta Oficial", "PA", "gazette", True, 60),
    Source("br_jucesp", "Brazil Junta Comercial (state registries)", "BR", "corporate", False, 30),
]

# --- Aircraft / vessels (cross-jurisdiction) -------------------------------
_TRANSPORT = [
    Source("imo_gisis", "IMO GISIS ship data", "GLOBAL", "vessel", False, 30),
    Source("equasis_vessels", "Equasis vessel information", "GLOBAL", "vessel", True, 60),
]

DEFAULT_ALLOWLIST = SourceAllowlist(
    _SANCTIONS + _FORESIGHT + _FOOTPRINT + _UK + _US
    + _EU + _ASIA + _ME + _OFFSHORE + _TRANSPORT
)
