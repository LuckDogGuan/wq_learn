"""Cross-platform (Windows/Linux) environment, protected-asset & AST self-check script.

Complies with experience_profile.md #5 (Environment check first) and #4/#7 (Static import verification).
"""
from __future__ import annotations

import ast
import importlib
import platform
import sqlite3
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

V2_ROOT = Path(__file__).resolve().parent
REPO_ROOT = V2_ROOT.parent
SRC_DIR = V2_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=== wq_research_v2 Cross-Platform Environment Check ===")
    print(f"OS      : {platform.platform()}")
    print(f"Python  : {sys.version.split()[0]}")
    ok = True

    if sys.version_info < (3, 11):
        print("[FAIL] Python >= 3.11 required")
        ok = False

    # 1. Core library imports
    for mod_name in ("requests", "pandas", "numpy", "yaml", "msgpack", "pytest", "sqlite3"):
        try:
            m = importlib.import_module(mod_name)
            ver = getattr(m, "__version__", "stdlib")
            print(f"[OK]   import {mod_name:<10} ({ver})")
        except Exception as exc:
            print(f"[FAIL] import {mod_name:<10}: {exc}")
            ok = False

    # 2. America/New_York DST clock
    try:
        tz = ZoneInfo("America/New_York")
        print(f"[OK]   ZoneInfo('America/New_York') -> {tz}")
    except Exception as exc:
        print(f"[FAIL] ZoneInfo('America/New_York'): {exc}")
        ok = False

    # 3. Critical workspace paths & hard-protected assets
    checks = [
        ("Password/config.yaml", REPO_ROOT / "Password" / "config.yaml"),
        ("WebDataScope-1.0.6/data", REPO_ROOT / "WebDataScope-1.0.6" / "data"),
        ("legacy_core/Core/runtime_data", REPO_ROOT / "legacy_core" / "Core" / "runtime_data"),
        ("reference/benchmarks/TopUser_2026Q4.txt", REPO_ROOT / "reference" / "benchmarks" / "TopUser_2026Q4.txt"),
        ("docs/整理与研究/00_索引.md", REPO_ROOT / "docs" / "整理与研究" / "00_索引.md"),
    ]
    for label, path in checks:
        if path.exists():
            extra = ""
            if label.endswith("runtime_data"):
                cnt = sum(1 for p in path.rglob("*") if p.is_file())
                extra = f" ({cnt} files)"
                if cnt != 1532:
                    print(f"[FAIL] {label} expected 1532 files, got {cnt}")
                    ok = False
                    continue
            print(f"[OK]   path   {label}{extra}")
        else:
            print(f"[WARN] missing path: {label}")

    # 4. SQLite WAL writability check in data/
    data_dir = REPO_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    probe_db = data_dir / "_env_probe.db"
    try:
        con = sqlite3.connect(str(probe_db))
        mode = con.execute("PRAGMA journal_mode=WAL;").fetchone()[0]
        con.close()
        for suf in ("", "-wal", "-shm"):
            p = Path(str(probe_db) + suf)
            if p.exists():
                p.unlink()
        print(f"[OK]   SQLite WAL in data/ (mode={mode})")
    except Exception as exc:
        print(f"[FAIL] SQLite WAL check: {exc}")
        ok = False

    # 5. AST syntax & forbidden security pattern check on all wq_research_v2/*.py
    py_files = sorted(V2_ROOT.rglob("*.py"))
    for pf in py_files:
        src = pf.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(pf))
        except SyntaxError as exc:
            print(f"[FAIL] AST syntax error in {pf}: {exc}")
            ok = False
        if "tests" not in pf.parts and pf.name != "check_env.py":
            if "verify=False" in src or "127.0.0.1:7897" in src:
                print(f"[FAIL] Security violation in {pf}: verify=False or hardcoded proxy detected")
                ok = False
    print(f"[OK]   AST & security scan passed ({len(py_files)} Python files)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
