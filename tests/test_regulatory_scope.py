from wealth_exposure.inference.regulatory_scope import RuleScope, probability_in_scope


def test_full_match_high_probability_unconfirmed():
    rule = RuleScope("FCA-PS25-12",
                     {"permission": "emoney_institution", "status": "authorised"})
    firm = {"permission": "emoney_institution", "status": "authorised"}
    out = probability_in_scope(rule, firm)
    assert out["probability_in_scope"] == 1.0
    assert out["label"] == "in scope on public criteria, unconfirmed by firm"
    assert out["missing_attributes"] == []


def test_partial_match_labelled_unconfirmed():
    rule = RuleScope("FCA-PS25-12",
                     {"permission": "emoney_institution", "status": "authorised"})
    firm = {"permission": "payment_institution", "status": "authorised"}
    out = probability_in_scope(rule, firm)
    assert out["probability_in_scope"] == 0.5
    assert "permission" in out["missing_attributes"]
    assert out["label"] == "in scope on public criteria, unconfirmed by firm"
