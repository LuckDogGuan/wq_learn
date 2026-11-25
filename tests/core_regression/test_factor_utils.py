import unittest
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))

from Core.factor.filter.factor_utils import filter_by_metrics, filter_by_keywords, analyze_keyword_frequency

class TestFactorUtils(unittest.TestCase):
    def setUp(self):
        # 构造一份假的因子数
        data = {
            'id': ['alpha_test_1', 'beta_test_2', 'alpha_beta_3', 'gamma_4'],
            'coverage': [0.1, 0.5, 0.8, 0.05],
            'dateCoverage': [1.0, 0.4, 0.8, 0.9],
            'alphaCount': [10, 100, 2, 50],
            'valueScore': [5.0, 7.5, 9.0, 3.0]
        }
        self.df = pd.DataFrame(data)

    def test_filter_by_metrics(self):
        # 测试 coverage 过滤
        res = filter_by_metrics(self.df, min_coverage=0.2)
        self.assertEqual(len(res), 2)
        self.assertNotIn('alpha_test_1', res['id'].tolist())

        # 测试 dateCoverage 过滤；它与 coverage 是独立条件。
        res_date = filter_by_metrics(self.df, min_date_coverage=0.6)
        self.assertEqual(res_date['id'].tolist(), ['alpha_test_1', 'alpha_beta_3', 'gamma_4'])

        # 测试 valueScore 过滤
        res2 = filter_by_metrics(self.df, min_value_score=6.0)
        self.assertEqual(len(res2), 2)

    def test_filter_by_keywords(self):
        # 测试单个关键
        res = filter_by_keywords(self.df, keywords=['alpha'])
        self.assertEqual(len(res), 2)

        # 测试多个关键 match_all=True
        res2 = filter_by_keywords(self.df, keywords=['alpha', 'beta'], match_all=True)
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2.iloc[0]['id'], 'alpha_beta_3')

    def test_analyze_keyword_frequency(self):
        # 词频统计
        res = analyze_keyword_frequency(self.df, min_count=0)
        self.assertIn('alpha', res)
        self.assertIn('test', res)
        self.assertEqual(res['alpha'], 2)

if __name__ == '__main__':
    unittest.main()
