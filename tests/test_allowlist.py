from wealth_exposure.allowlist import DEFAULT_ALLOWLIST


def test_allowlist_is_comprehensive():
    assert len(DEFAULT_ALLOWLIST) >= 60


def test_core_sources_present_and_automatable():
    for sid in ("uk_companies_house", "uk_gazette", "breach_licensed_provider",
                "us_sec_edgar", "ofac_sdn"):
        assert DEFAULT_ALLOWLIST.contains(sid)
    assert DEFAULT_ALLOWLIST.get("uk_companies_house").terms_permit_automation


def test_restricted_sources_marked_non_automatable():
    # Paid / access-restricted sources must not be auto-collected by default.
    for sid in ("us_pacer", "hk_icris", "sg_acra_bizfile", "uk_land_registry_title"):
        assert DEFAULT_ALLOWLIST.get(sid).terms_permit_automation is False


def test_filters_by_jurisdiction_and_category():
    uk_ids = {s.source_id for s in DEFAULT_ALLOWLIST.by_jurisdiction("UK")}
    assert "uk_companies_house" in uk_ids
    sanctions_ids = {s.source_id for s in DEFAULT_ALLOWLIST.by_category("sanctions")}
    assert {"ofac_sdn", "ofsi_sanctions", "un_sc_sanctions"} <= sanctions_ids


def test_no_off_register_or_leaked_sources():
    # Sanity: nothing in the catalogue is a leaked/stolen-data source.
    assert not DEFAULT_ALLOWLIST.contains("leaked_database")
    assert not DEFAULT_ALLOWLIST.contains("stolen_data_dump")
