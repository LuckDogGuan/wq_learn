"""Compatibility entry for explicit database maintenance."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Core.tools.maintenance.clean_db import clean_database

if __name__ == "__main__":
    import runpy
    runpy.run_module("Core.tools.maintenance.clean_db", run_name="__main__")
