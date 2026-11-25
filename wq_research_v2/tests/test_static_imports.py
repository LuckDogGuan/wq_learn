"""Static AST, import completeness, and security invariant tests (experience_profile #4/#7)."""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

V2_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = V2_ROOT / "src" / "wq_research_v2"


def test_all_python_files_parse_cleanly() -> None:
    files = list(V2_ROOT.rglob("*.py"))
    assert len(files) >= 15
    for p in files:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def test_all_modules_import_without_error() -> None:
    for p in sorted(SRC_DIR.glob("*.py")):
        if p.name == "__main__.py":
            continue
        mod_name = "wq_research_v2" if p.name == "__init__.py" else f"wq_research_v2.{p.stem}"
        mod = importlib.import_module(mod_name)
        assert mod is not None


def test_zero_insecure_patterns_or_submit_calls_in_src() -> None:
    for p in sorted(SRC_DIR.glob("*.py")):
        src = p.read_text(encoding="utf-8")
        assert "verify=False" not in src, f"verify=False forbidden in {p}"
        assert "127.0.0.1:7897" not in src, f"Hardcoded proxy forbidden in {p}"
        # Only auth_session's explicit PermissionError guard mentions '/submit'
        if p.name != "auth_session.py":
            assert "/alphas/{alpha_id}/submit" not in src, f"Submit call forbidden in {p}"
            assert "submit_alpha" not in src, f"Submit helper forbidden in {p}"
