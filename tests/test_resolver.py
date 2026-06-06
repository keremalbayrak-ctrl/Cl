from wealth_exposure.resolver import Resolver


def test_two_source_confirmation():
    r = Resolver(consent=None)
    records = [
        {"claims": [{"key": "addr:1 High St", "source": "uk_companies_house"}]},
        {"claims": [{"key": "addr:1 High St", "source": "uk_land_registry"}]},
        {"claims": [{"key": "control:client-1", "source": "uk_companies_house"}]},
    ]
    out = r.correlate(records)
    established = {e["claim"] for e in out["established"]}
    unconfirmed = {u["claim"] for u in out["unconfirmed"]}
    assert "addr:1 High St" in established  # confirmed by two sources
    assert "control:client-1" in unconfirmed  # only one source
