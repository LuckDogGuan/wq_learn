import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))


class ImportSafetyTests(unittest.TestCase):
    def test_diagnostic_and_cleanup_modules_have_no_import_side_effects(self):
        modules = (
            "Core.test.clean",
            "Core.test.clean_db",
            "Core.tests.run_all",
            "Core.factor.filter.alpha_evaluator",
            "Core.catalog_sync",
            "Core.tools.maintenance.clean",
            "Core.tools.maintenance.clean_db",
        )
        with patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("import attempted HTTP"),
        ), patch(
            "sqlite3.connect",
            side_effect=AssertionError("import attempted database mutation"),
        ):
            for module in modules:
                with self.subTest(module=module):
                    sys.modules.pop(module, None)
                    importlib.import_module(module)


if __name__ == "__main__":
    unittest.main()
