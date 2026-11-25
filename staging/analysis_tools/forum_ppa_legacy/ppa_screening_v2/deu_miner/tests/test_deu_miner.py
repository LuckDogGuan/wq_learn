import unittest
import os
import sys

# add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deu_miner.evaluator import evaluate_metrics
from deu_miner.config import HARD_THRESHOLDS
from deu_miner.alpha_generator import load_datefields_datasets

class TestDeuMiner(unittest.TestCase):
    def test_evaluate_metrics_pass(self):
        details = {
            'is': {
                'sharpe': 1.6,
                'fitness': 1.1,
                'margin': 0.0011, # 11bp
                'turnover': 0.15,
                'checks': [{'name': 'LOW_2Y_SHARPE', 'value': 1.7}]
            }
        }
        passed, reason = evaluate_metrics(details)
        self.assertTrue(passed, f"Expected to pass, but failed: {reason}")

    def test_evaluate_metrics_fail_sharpe(self):
        details = {
            'is': {
                'sharpe': 1.5,
                'fitness': 1.1,
                'margin': 0.0011, 
                'turnover': 0.15,
                'checks': [{'name': 'LOW_2Y_SHARPE', 'value': 1.7}]
            }
        }
        passed, reason = evaluate_metrics(details)
        self.assertFalse(passed)
        self.assertEqual(reason, "Low Sharpe")

    def test_load_datefields_datasets(self):
        try:
            datasets = load_datefields_datasets()
            self.assertTrue(len(datasets) > 0)
        except FileNotFoundError:
            self.skipTest("CSV file not found locally to run the test.")

if __name__ == '__main__':
    unittest.main()
