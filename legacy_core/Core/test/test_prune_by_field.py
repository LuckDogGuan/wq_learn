"""运行此文件可查看 Alpha 剪枝前后差异；不访问平台、不创建回测。"""
import sys
import unittest
from pathlib import Path


def find_core_parent():
    """从 Core/test 向上定位包含 Core 包的父目录，兼容直接运行此 .py 文件。"""
    for directory in Path(__file__).resolve().parents:
        if (directory / "Core" / "__init__.py").is_file():
            return directory
    raise RuntimeError("无法定位 Core 包的父目录，请确认文件位于 代码/优化代码/Core/test/ 下")


CORE_PARENT = find_core_parent()
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

from Core.sim.alpha_manager import prune


# 与 Alpha_Test copy.ipynb 的一阶字段相同，测试不依赖本地 catalog 或平台登录。
FIELD_IDS = [
    "eps_revision_magnitude",
    "fnd6_newa2_oibdp",
    "directional_indicator",
    "adaptive_similarity_upward_breakaway_gap_120",
]


def alpha_record(alpha_id, expression, sharpe, recommended_decay=6):
    """构造 get_alphas 返回格式的最小示例记录。"""
    return [alpha_id, expression, sharpe, 0.20, 1.0, 0.001, "2026-08-22", 6, recommended_decay]


def print_records(title, records):
    print(f"\n{title}（{len(records)} 个）")
    for record in records:
        print(f"  Sharpe={record[2]:>4}: {record[1]}")


class PruneByFieldTests(unittest.TestCase):
    def setUp(self):
        # 同一个 EPS 字段有 4 个不同窗口；Top 2 后应仅留下 Sharpe 2.20 与 2.05。
        # 同一对字段的两种模板也共同竞争 Top 2；字段顺序反转则保留为另一经济方向组。
        self.records = [
            alpha_record("eps-5", "group_rank(ts_rank(eps_revision_magnitude, 5), industry)", 2.20),
            alpha_record("eps-22", "group_rank(ts_rank(eps_revision_magnitude, 22), industry)", 2.05),
            alpha_record("eps-66", "group_rank(ts_rank(eps_revision_magnitude, 66), industry)", 1.80),
            alpha_record("eps-120", "group_rank(ts_rank(eps_revision_magnitude, 120), industry)", 1.55),
            alpha_record(
                "pair-diff", "group_rank(rank(eps_revision_magnitude) - rank(fnd6_newa2_oibdp), industry)", 1.95
            ),
            alpha_record(
                "pair-zscore", "group_rank(ts_zscore(eps_revision_magnitude - fnd6_newa2_oibdp, 63), industry)", 1.72
            ),
            alpha_record(
                "pair-low", "group_rank(ts_rank(eps_revision_magnitude - fnd6_newa2_oibdp, 120), industry)", 1.20
            ),
            alpha_record(
                "pair-reverse", "group_rank(rank(fnd6_newa2_oibdp) - rank(eps_revision_magnitude), industry)", 1.88
            ),
            alpha_record("insider-5", "group_rank(ts_rank(directional_indicator, 5), industry)", 1.70),
            alpha_record("insider-22", "group_rank(ts_rank(directional_indicator, 22), industry)", 1.40),
            alpha_record(
                "pattern-20", "group_rank(ts_rank(adaptive_similarity_upward_breakaway_gap_120, 20), industry)", 1.60
            ),
        ]

    def test_field_ids_make_the_before_after_difference_visible(self):
        print_records("剪枝前", self.records)

        # prefix='' 没有字段信息：每个不同公式各成一组，几乎不会削减。
        without_field_ids = prune(self.records, prefix="", keep_num=2)
        self.assertEqual(len(without_field_ids), len(self.records))

        # 传入 Notebook 的字段清单后：每个“字段组合 + 顺序 + 方向”只保留 Top 2。
        pruned = prune(self.records, field_ids=FIELD_IDS, keep_num=2)
        original_by_expression = {record[1]: record for record in self.records}
        retained_records = [original_by_expression[expression] for expression, _ in pruned]
        print_records(
            "剪枝后：EPS 单字段 4 个变体只留 2 个；同序双字段模板共同竞争；反序双字段单独保留",
            retained_records,
        )

        kept = {expression for expression, _ in pruned}
        self.assertIn("ts_rank(eps_revision_magnitude, 5)", "\n".join(kept))
        self.assertIn("ts_rank(eps_revision_magnitude, 22)", "\n".join(kept))
        self.assertNotIn("ts_rank(eps_revision_magnitude, 66)", "\n".join(kept))
        self.assertNotIn("ts_rank(eps_revision_magnitude, 120)", "\n".join(kept))
        self.assertNotIn("ts_rank(eps_revision_magnitude - fnd6_newa2_oibdp, 120)", "\n".join(kept))
        self.assertEqual(len(pruned), 8)

    def test_positive_and_negative_candidates_have_separate_top_n(self):
        """track 模式中，正、负 Sharpe 是两条不同经济方向，不应互相挤掉。"""
        records = [
            alpha_record("pos-best", "rank(eps_revision_magnitude)", 2.10),
            alpha_record("pos-low", "ts_rank(eps_revision_magnitude, 22)", 1.40),
            alpha_record("neg-best", "-rank(eps_revision_magnitude)", -2.30),
            alpha_record("neg-low", "-ts_rank(eps_revision_magnitude, 22)", -1.50),
        ]

        pruned = prune(records, field_ids=FIELD_IDS, keep_num=1)
        kept = {expression for expression, _ in pruned}

        # 每个方向各留一个最强候选，而非只留下正向 Sharpe 最大的一个。
        self.assertEqual(kept, {"rank(eps_revision_magnitude)", "-rank(eps_revision_magnitude)"})

    def test_unknown_fields_are_not_merged_or_deleted(self):
        """近期窗口若混入非本批字段，保守保留，避免错误归入 selected_ids 的组。"""
        records = [
            alpha_record("known", "rank(eps_revision_magnitude)", 1.80),
            alpha_record("unknown-1", "rank(unrelated_field_a)", 1.70),
            alpha_record("unknown-2", "rank(unrelated_field_b)", 1.60),
        ]

        pruned = prune(records, field_ids=FIELD_IDS, keep_num=1)
        self.assertEqual(len(pruned), 3)

    def test_keep_num_must_be_positive(self):
        """避免 keep_num=0 时悄悄丢弃全部候选。"""
        with self.assertRaises(ValueError):
            prune(self.records, field_ids=FIELD_IDS, keep_num=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
