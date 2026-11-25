"""Unit tests for tunable similar-seed pruner (non-destructive fast-inference pruning)."""
from __future__ import annotations

from wq_research_v2.seed_pruner import PruningConfig, prune_similar_seeds


def test_pruner_drops_near_duplicate_window_and_metric_clones_keeping_best() -> None:
    seeds = [
        {
            "alpha_id": "N1K03xae", "region": "USA", "dataset_id": "price_signal_dl",
            "primary_field_id": "raw_volume_indicator_6", "sharpe": 1.10, "sharpe_2y": 1.84,
            "turnover": 0.0371, "fitness": 0.67, "margin": 0.00249,
            "expression": "group_rank(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10), subindustry)",
        },
        {
            "alpha_id": "xAl6KWkp", "region": "USA", "dataset_id": "price_signal_dl",
            "primary_field_id": "raw_volume_indicator_6", "sharpe": 1.10, "sharpe_2y": 1.85,
            "turnover": 0.0349, "fitness": 0.67, "margin": 0.00264,
            "expression": "group_rank(ts_decay_linear(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 5), 10), subindustry)",
        },
        {
            "alpha_id": "gJrAY2bM", "region": "USA", "dataset_id": "price_signal_dl",
            "primary_field_id": "raw_volume_indicator_6", "sharpe": 1.06, "sharpe_2y": 1.99,
            "turnover": 0.0266, "fitness": 0.63, "margin": 0.00334,
            "expression": "group_rank(ts_decay_linear(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 22), 10), subindustry)",
        },
        {
            "alpha_id": "diffField1", "region": "USA", "dataset_id": "price_signal_dl",
            "primary_field_id": "raw_trend_indicator_6", "sharpe": 0.95, "sharpe_2y": 1.40,
            "turnover": 0.0800, "fitness": 0.50, "margin": 0.0012,
            "expression": "signed_power(group_zscore(ts_mean(ts_backfill(raw_trend_indicator_6, 21), 22), subindustry), 1.5)",
        },
    ]
    kept, pruned = prune_similar_seeds(seeds, config=PruningConfig(jaccard_max=0.78, max_per_field=2, max_per_dataset=6))
    kept_ids = [s["alpha_id"] for s in kept]
    assert "xAl6KWkp" in kept_ids  # highest (1.10, 2Y 1.85) kept
    assert "diffField1" in kept_ids  # structurally distinct field/operator kept
    assert len(pruned) == 2  # N1K03xae & gJrAY2bM pruned as near-identical clones!


def test_pruner_respects_tunable_caps() -> None:
    seeds = [
        {
            "alpha_id": f"A{i}", "region": "EUR", "dataset_id": "model25",
            "primary_field_id": f"field_{i}", "sharpe": 2.0 - i * 0.1, "turnover": 0.05 + i * 0.02,
            "expression": f"group_zscore(field_{i}, industry)",
        }
        for i in range(10)
    ]
    kept, pruned = prune_similar_seeds(seeds, config=PruningConfig(jaccard_max=0.95, max_per_field=1, max_per_dataset=4))
    assert len(kept) == 4
    assert len(pruned) == 6
    assert [s["alpha_id"] for s in kept] == ["A0", "A1", "A2", "A3"]
