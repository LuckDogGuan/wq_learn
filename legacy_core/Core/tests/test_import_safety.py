"""Compatibility test entry; canonical tests live in testFile/core_regression."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from testFile.core_regression import test_import_safety as _tests


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(_tests)


if __name__ == "__main__":
    unittest.main()
