"""Unit tests for wq_research_v2.experience_reuser (Route ④ historical experience reuse)."""
from __future__ import annotations

from pathlib import Path

from wq_research_v2.experience_reuser import ExperienceReuser


def test_experience_reuser_loads_workspace_sources() -> None:
    reuser = ExperienceReuser()
    status = reuser.sources_status()
    assert status["optimization_ledger"] is True
    assert status["reusable_experience_rules"] is True
    assert status["sc_pass_pc_rescue_queue"] is True


def test_experience_reuser_matches_usa_high_pc_and_warnings() -> None:
    reuser = ExperienceReuser()
    pkt = reuser.retrieve(
        region="USA",
        universe="TOP3000",
        dataset_id="ai_equity_alpha",
        neutralization="REVERSION_AND_MOMENTUM",
        failure_code="HIGH_PC",
        operators=["tail", "hump"],
    )
    eff_ids = {x.item_id for x in pkt.effective_lessons}
    assert any(cid in eff_ids for cid in ("EFF-26", "EFF-27", "EFF-02"))
    assert len(pkt.ineffective_warnings) >= 1
    assert len(pkt.empirical_rules) >= 1

    card = pkt.render_compact_markdown(max_bytes=3200)
    assert "历史经验复用卡" in card
    assert len(card.encode("utf-8")) <= 3400  # small room for truncation footer if triggered


def test_experience_reuser_recalls_asi_lessons_and_crowding_prior() -> None:
    reuser = ExperienceReuser()
    pkt = reuser.retrieve(
        region="ASI",
        universe="MINVOL1M",
        dataset_id="multifactor_return_pred",
        failure_code="LOW_ASI_JPN_SHARPE",
    )
    eff_ids = {x.item_id for x in pkt.effective_lessons}
    ineff_ids = {x.item_id for x in pkt.ineffective_warnings}
    assert len(eff_ids) >= 1
    assert len(ineff_ids) >= 1

    prior = reuser.score_direction_crowding_prior(region="ASI", dataset_id="multifactor_return_pred")
    assert prior["sample_count"] >= 1
    assert prior["crowding_level"] in ("PASSABLE_PRIOR", "BORDERLINE_PRIOR", "HIGH_CROWDING_PRIOR")

    unknown_prior = reuser.score_direction_crowding_prior(region="KOR", dataset_id="nonexistent_ds_xyz")
    assert unknown_prior["crowding_level"] == "UNKNOWN"
    assert unknown_prior["sample_count"] == 0


def test_experience_reuser_gracefully_handles_missing_optional_skill_file(tmp_path: Path) -> None:
    reuser = ExperienceReuser(skill_rules_jsonl_path=tmp_path / "missing_rules.jsonl")
    assert reuser.sources_status()["worldquant_experience_reuse_skill"] is False
    pkt = reuser.retrieve(region="EUR", dataset_id="model77", failure_code="LOW_SUB_UNIVERSE_SHARPE")
    assert len(pkt.effective_lessons) >= 1
    assert pkt.to_dict()["query"]["region"] == "EUR"
