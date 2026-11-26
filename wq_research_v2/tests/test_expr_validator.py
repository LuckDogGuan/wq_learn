"""Tests for all 10 hard static gates in ExprValidator (D1-Only, Decision #3, Gold-81, 42 defects, Alphas=0)."""
from __future__ import annotations

from wq_research_v2.expr_validator import ExprValidator


def _base_settings(**overrides) -> dict:
    s = {
        "region": "DEU",
        "universe": "TOP500",
        "delay": 1,
        "neutralization": "INDUSTRY",
        "decay": 0,
        "truncation": 0.08,
        "visualization": False,
    }
    s.update(overrides)
    return s


def test_user_canonical_dual_branch_expression_passes() -> None:
    v = ExprValidator()
    expr = (
        "reverse(min("
        "rank(ts_delta(ts_backfill(vec_avg(snt26_top50pctranking),500),55)), "
        "rank(ts_decay_linear(ts_backfill(mad_underweight_rating_score,5),378))"
        "))"
    )
    rep = v.validate(expr, _base_settings())
    assert rep.valid, rep.errors
    assert "snt26_top50pctranking" in rep.fields_used
    assert "mad_underweight_rating_score" in rep.fields_used
    # ts_backfill (2 calls) must be excluded from counted ops: reverse, min, rank, ts_delta, vec_avg, rank, ts_decay_linear = 7
    assert rep.total_counted_calls == 7


def test_delay_0_blocked() -> None:
    rep = ExprValidator().validate("rank(mdl264_1l_fmc)", _base_settings(delay=0))
    assert not rep.valid
    assert any("D1-Only" in e for e in rep.errors)


def test_decision_3_forbids_add_multiply_trade_when() -> None:
    v = ExprValidator()
    for expr in [
        "rank(x) + rank(y)",
        "add(rank(x), rank(y))",
        "-1 * rank(x)",
        "multiply(rank(x), rank(y))",
        "trade_when(volume > 0, rank(x), -1)",
    ]:
        rep = v.validate(expr, _base_settings())
        assert not rep.valid, f"Expected rejection for {expr}"


def test_missing_gold_operators_blocked() -> None:
    v = ExprValidator()
    for expr in [
        "ts_median(x, 20)",
        "left_tail(rank(x), maximum=0.2)",
        "right_tail(rank(x), minimum=0.8)",
        "generalized_rank(x, m=1)",
        "hump_decay(x, p=0.1)",
        "ts_decay_exp_window(x, 20, factor=0.5)",
        "clamp(rank(x), lower=0.2, upper=0.8)",
        "tanh(zscore(x))",
        "s_log_1p(zscore(x))",
        "arc_tan(zscore(x))",
        "group_median(x, subindustry)",
        "keep(rank(x), y, period=45)",
        "vector_proj(rank(x), rank(adv20))",
    ]:
        rep = v.validate(expr, _base_settings())
        assert not rep.valid, f"Expected Gold-level rejection for {expr}"


def test_signature_and_behavioral_traps() -> None:
    v = ExprValidator()
    assert not v.validate("hump(rank(x), 0.01)", _base_settings()).valid
    assert v.validate("hump(rank(x), hump=0.01)", _base_settings()).valid
    assert not v.validate("rank(x)", _base_settings(neutralization="RAM")).valid
    assert v.validate("rank(x)", _base_settings(neutralization="REVERSION_AND_MOMENTUM")).valid
    assert not v.validate("ts_decay_linear(rank(x), 5)", _base_settings()).valid
    assert v.validate("ts_decay_linear(rank(x), 5, dense=true)", _base_settings()).valid
    assert v.validate("rank(ts_decay_linear(x, 5))", _base_settings()).valid
    assert not v.validate("ts_target_tvr_decay(rank(x), lambda_max=2, target_tvr=0.1)", _base_settings()).valid
    assert v.validate("ts_target_tvr_decay(rank(x), lambda_min=0, lambda_max=1, target_tvr=0.1)", _base_settings()).valid


def test_42_defect_templates_and_trap_fields_blocked() -> None:
    v = ExprValidator()
    for bad in [
        "2.-ts_rank(ts_std_dev(x, 66), 252)",
        "ts_mean(x, 252) > 100",
        "group_mean(x, 1, market)",
        "ts_backfill(ts_backfill(x, 120), 120)",
        "group_neutralize(group_zscore(x, industry), industry)",
        "ts_backfill(x, 1200)",
        "rank(anl93_best_analyst)",
        "rank(mdl307_cusip)",
    ]:
        rep = v.validate(bad, _base_settings())
        assert not rep.valid, f"Expected defect rejection for {bad}"


def test_alpha0_purity_guard() -> None:
    v = ExprValidator()
    expr = "group_rank(mdl264_1l_fmc, industry)"
    assert v.validate(expr, _base_settings(), queue_type="UNUSED_ALPHA0", field_alpha_counts={"mdl264_1l_fmc": 0}).valid
    # Mixing even 1 field with alphaCount > 0 must fail UNUSED_ALPHA0 purity
    mixed = "min(rank(mdl264_1l_fmc), rank(used_field))"
    rep = v.validate(
        mixed, _base_settings(), queue_type="UNUSED_ALPHA0",
        field_alpha_counts={"mdl264_1l_fmc": 0, "used_field": 3},
    )
    assert not rep.valid
    assert any("purity failed" in e for e in rep.errors)
