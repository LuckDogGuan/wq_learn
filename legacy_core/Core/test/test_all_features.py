"""Compatibility entry for the unified offline Core review suite."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from testFile.core_regression.run_review_suite import main

if __name__ == "__main__":
    raise SystemExit(main())
