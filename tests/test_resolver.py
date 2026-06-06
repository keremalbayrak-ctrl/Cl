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


def test_normalize_and_name_variants():
    r = Resolver()
    assert r.normalize_name("Açme Holdings Ltd") == r.normalize_name("ACME, Inc.") == "acme"
    groups = r.resolve_name_variants(["Açme Holdings Ltd", "ACME, Inc.", "Beta LLC"])
    assert sorted(groups["acme"]) == ["ACME, Inc.", "Açme Holdings Ltd"]
    assert "beta" in groups


def test_build_network_edges():
    r = Resolver()
    edges = r.build_network([{"nodes": ["A", "B", "C"]}, {"nodes": ["A", "B"]}])
    weights = {tuple(e["edge"]): e["weight"] for e in edges}
    assert weights[("A", "B")] == 2
    assert weights[("A", "C")] == 1


def test_correlate_by_address():
    r = Resolver()
    shared = r.correlate_by_address([
        {"subject": "ENT-1", "address": "1 High St, London"},
        {"subject": "ENT-2", "address": "1 High St  London."},
        {"subject": "ENT-3", "address": "9 Other Rd"},
    ])
    # ENT-1 and ENT-2 normalise to the same address; ENT-3 stands alone.
    assert any(set(v) == {"ENT-1", "ENT-2"} for v in shared.values())
