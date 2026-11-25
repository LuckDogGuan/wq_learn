"""Offline unit tests for Guangzhou-style Useful tagger & low-memory D1 streaming scanner."""
from __future__ import annotations

from unittest.mock import MagicMock

from wq_research_v2.tagger import (
    PC_HIGH_TAG,
    SC_HIGH_TAG,
    USEFUL_TAG,
    apply_alpha_tag,
    compute_merged_tags,
    iter_unsubmitted_d1_window,
)


def test_compute_merged_tags_idempotent_and_conflict_free() -> None:
    merged, changed = compute_merged_tags(["AQP202611"], USEFUL_TAG)
    assert merged == ["Useful", "AQP202611"]
    assert changed is True

    merged2, changed2 = compute_merged_tags(["Useful", "AQP202611"], USEFUL_TAG)
    assert merged2 == ["Useful", "AQP202611"]
    assert changed2 is False

    # Adding SC_IS_HIGHT must automatically strip stale Useful tag
    merged3, changed3 = compute_merged_tags(["Useful", "AQP202611"], SC_HIGH_TAG)
    assert "Useful" not in merged3
    assert SC_HIGH_TAG in merged3 and "AQP202611" in merged3
    assert changed3 is True

    # Adding PC_IS_HIGHT also strips stale Useful
    merged4, _ = compute_merged_tags(["Useful"], PC_HIGH_TAG)
    assert merged4 == [PC_HIGH_TAG]


def test_apply_alpha_tag_dry_run_default_and_confirmed_patch() -> None:
    client = MagicMock()
    client.get.return_value = MagicMock(status_code=200, json=lambda: {"tags": []})
    client.patch.return_value = MagicMock(status_code=200)

    # Dry-run never calls PATCH
    dry = apply_alpha_tag(client, "A123", USEFUL_TAG, confirm_apply=False)
    assert dry["applied"] is False
    assert dry["dry_run"] is True
    assert dry["merged_tags"] == ["Useful"]
    client.patch.assert_not_called()

    # Confirmed apply calls PATCH with explicit_user_confirmed=True
    live = apply_alpha_tag(client, "A123", USEFUL_TAG, confirm_apply=True)
    assert live["applied"] is True
    client.patch.assert_called_once_with(
        "/alphas/A123",
        explicit_user_confirmed=True,
        json={"tags": ["Useful"]},
        timeout=30,
    )


def test_low_memory_streaming_scanner_pushes_d1_filters_and_skips_terminal_tags() -> None:
    client = MagicMock()
    client.get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "results": [
                {
                    "id": "GOOD_D1",
                    "type": "REGULAR",
                    "dateCreated": "2026-11-24T10:00:00Z",
                    "tags": [],
                    "settings": {"region": "GBR", "universe": "TOP700", "delay": 1},
                    "is": {"sharpe": 2.1, "fitness": 1.4, "turnover": 0.2, "margin": 0.0012},
                },
                {
                    "id": "SKIP_SC_HIGH",
                    "type": "REGULAR",
                    "dateCreated": "2026-11-24T10:00:00Z",
                    "tags": ["SC_IS_HIGHT"],
                    "settings": {"region": "GBR", "universe": "TOP700", "delay": 1},
                    "is": {"sharpe": 2.5, "fitness": 1.8, "turnover": 0.2, "margin": 0.0015},
                },
                {
                    "id": "SKIP_D0",
                    "type": "REGULAR",
                    "dateCreated": "2026-11-24T10:00:00Z",
                    "tags": [],
                    "settings": {"region": "USA", "universe": "TOP3000", "delay": 0},
                    "is": {"sharpe": 3.0, "fitness": 2.0},
                },
            ]
        },
    )

    items = list(iter_unsubmitted_d1_window(client, start_iso="2026-11-24T00:00:00Z", region="GBR"))
    assert [x.alpha_id for x in items] == ["GOOD_D1"]
    assert items[0].margin_bp == 12.0
    called_url = client.get.call_args[0][0]
    assert "settings.delay=1" in called_url
    assert "status=UNSUBMITTED" in called_url
    assert "settings.region=GBR" in called_url
