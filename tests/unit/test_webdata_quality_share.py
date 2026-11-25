import importlib.util
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

import msgpack


MODULE_PATH = Path(__file__).parents[1] / "tools" / "webdata_quality.py"
SPEC = importlib.util.spec_from_file_location("webdata_quality", MODULE_PATH)
webdata_quality = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(webdata_quality)


def packed(value):
    return zlib.compress(msgpack.packb(value, use_bin_type=True))


class WebDataQualityUniverseTest(unittest.TestCase):
    def test_normalizes_coordinates(self):
        self.assertEqual(webdata_quality.normalize_coordinate(" glb ", "region"), "GLB")
        self.assertEqual(
            webdata_quality.normalize_coordinate("illiquid_minvol1m", "universe"),
            "ILLIQUID_MINVOL1M",
        )

    def test_lists_and_ranks_universe_field_health(self):
        healthy = {
            "field_a": {"CoverageRatio": [0.8, 0.9, 1.0]},
            "field_b": {"CoverageRatio": [0.7, 0.8, 0.9]},
        }
        sparse = {"field_c": {"CoverageRatio": [0.2, 0.3, 0.4]}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.zip"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("data/dataset_a_GLB_TOP3000_Delay1.bin", packed(healthy))
                zf.writestr(
                    "data/dataset_b_GLB_ILLIQUID_MINVOL1M_Delay1.bin",
                    packed(sparse),
                )
            with zipfile.ZipFile(path) as zf:
                rows = webdata_quality.make_universe_rows(
                    zf, "GLB", 1, sweet_datasets={"dataset_a"}
                )

        self.assertEqual([row["universe"] for row in rows], ["TOP3000", "ILLIQUID_MINVOL1M"])
        self.assertEqual(rows[0]["sweet_spot_dataset_count"], 1)
        self.assertEqual(rows[0]["community_performance_status"], "UNOBSERVED_BY_UNIVERSE")
        self.assertNotIn("category", rows[0])


if __name__ == "__main__":
    unittest.main()
