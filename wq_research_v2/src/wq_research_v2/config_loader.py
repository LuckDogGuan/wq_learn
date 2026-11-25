"""Workspace path discovery and declarative JSON config loader."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_DIR = Path(__file__).resolve().parent
V2_ROOT = PACKAGE_DIR.parents[1]
REPO_ROOT = V2_ROOT.parent
CONFIG_DIR = V2_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
LEDGER_DB_PATH = DATA_DIR / "wq_v2_ledger.db"
SC_CACHE_DB_PATH = DATA_DIR / "sc_cache_v2" / "os_pnl_cache.db"
WDS_DATA_DIR = REPO_ROOT / "WebDataScope-1.0.6" / "data"
LEGACY_CORE_DIR = REPO_ROOT / "legacy_core" / "Core"
LEGACY_RUNTIME_DATA_DIR = LEGACY_CORE_DIR / "runtime_data"
PASSWORD_CONFIG_PATH = REPO_ROOT / "Password" / "config.yaml"
RECORDS_DIR = REPO_ROOT / "docs" / "整理与研究" / "records"


def load_json_config(filename: str) -> dict[str, Any]:
    path = CONFIG_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def load_d1_thresholds() -> dict[str, Any]:
    return load_json_config("d1_thresholds.json")


def load_operators_config() -> dict[str, Any]:
    return load_json_config("operators_gold_81.json")


def load_buggy_templates_config() -> dict[str, Any]:
    return load_json_config("buggy_templates_blocklist.json")


def load_templates_50_50() -> dict[str, Any]:
    return load_json_config("templates_50_50.json")
