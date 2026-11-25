"""One offline entry for the Core review regression scope."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "legacy_core"))
sys.path.insert(0, str(ROOT / "legacy_core/pipelines/ra_screening"))
sys.path.insert(0, str(ROOT / "tests/unit"))


def main():
    with patch("requests.sessions.Session.request", side_effect=AssertionError("Live HTTP forbidden in review tests")):
        loader = unittest.TestLoader()
        suite = loader.discover(str(Path(__file__).parent), pattern="test_*.py")
        for name in (
            "test_filter_ra_alphas_v5",
        ):
            suite.addTests(loader.loadTestsFromName(name))
        result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
