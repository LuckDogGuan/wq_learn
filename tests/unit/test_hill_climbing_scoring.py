import math
import sys
import unittest
from pathlib import Path


HILL_ROOT = Path(__file__).parents[1] / '代码' / '优化代码' / '爬山代码'
if str(HILL_ROOT) not in sys.path:
    sys.path.insert(0, str(HILL_ROOT))

from hill_climbing.scoring import (
    evaluate_margin_repair_readiness,
    evaluate_stage_candidate,
    evaluate_stage_gate,
    is_candidate_better,
    margin_repair_rank_key,
    score_stage_metrics,
)


def stats(sharpe=2.0, fitness=1.3, margin=0.0015, sharpe_2y=2.0,
          turnover=0.15, passed=False, sc=0.2, pc=0.2):
    return locals()


class StageV2ScoringTest(unittest.TestCase):
    def test_gate_values_are_strictly_greater(self):
        for stage, exact in (
            (1, stats(1.2, 0.5, 0.0003, 1.0, 0.03)),
            (2, stats(1.4, 0.75, 0.0006, 1.3, 0.04)),
            (3, stats(1.58, 1.0, 0.001, 1.6, 0.05, True)),
        ):
            self.assertEqual(evaluate_stage_gate(exact, stage)['status'], 'FAIL')

    def test_score_is_monotone_diminishing_and_capped(self):
        values = [score_stage_metrics(stats(sharpe=value))['components']['sharpe']
                  for value in (1.5, 1.8, 2.4, 3.0, 3.6, 5.0)]
        self.assertEqual(values, sorted(values))
        self.assertGreater(values[1] - values[0], values[4] - values[3])
        self.assertEqual(values[-1], 30.0)
        capped = score_stage_metrics(
            stats(5.0, 4.0, 0.01, sharpe_2y=5.0), include_correlations=False
        )
        self.assertAlmostEqual(capped['score'], 100.0)
        self.assertAlmostEqual(capped['components']['margin'], 25.0)

    def test_margin_cannot_rescue_a_failed_gate(self):
        result = evaluate_stage_candidate(stats(sharpe=1.2, margin=0.02), 1)
        self.assertFalse(result['eligible'])
        self.assertGreaterEqual(result['components']['margin'], 25.0)

    def test_small_metric_tradeoff_uses_margin_then_2y_then_turnover(self):
        current = stats(2.1, 1.3, 0.0015, 1.8, 0.2)
        candidate = stats(2.0, 1.25, 0.0017, 1.8, 0.2)
        self.assertFalse(is_candidate_better(candidate, 60.1, current, 60.4))
        self.assertTrue(is_candidate_better(candidate, 60.45, current, 60.4))
        self.assertFalse(is_candidate_better(candidate, 59.8, current, 60.4))

    def test_three_stage_funnel_and_platform_pass_boundary(self):
        candidate = stats(1.55, 0.9, 0.0008, 1.55, 0.4, False)
        self.assertTrue(evaluate_stage_candidate(candidate, 1)['eligible'])
        self.assertTrue(evaluate_stage_candidate(candidate, 2)['eligible'])
        self.assertFalse(evaluate_stage_candidate(candidate, 3)['eligible'])
        final = stats(1.7, 1.1, 0.0011, 1.7, 0.2, False)
        self.assertTrue(evaluate_stage_gate(final, 2)['passed'])
        self.assertFalse(evaluate_stage_gate(final, 3)['passed'])
        final['passed'] = True
        self.assertTrue(evaluate_stage_gate(final, 3)['passed'])

    def test_both_correlations_are_lower_is_better_and_strict(self):
        low = score_stage_metrics(stats(sc=0.1, pc=0.1, passed=True), stage=3)
        high = score_stage_metrics(stats(sc=0.3, pc=0.6, passed=True), stage=3)
        self.assertGreater(low['score'], high['score'])
        self.assertGreater(high['penalties']['sc'], low['penalties']['sc'])
        self.assertGreater(high['penalties']['pc'], low['penalties']['pc'])
        self.assertFalse(evaluate_stage_gate(stats(sc=0.5), 1)['passed'])
        self.assertEqual(score_stage_metrics(stats(sc=math.nan))['status'], 'PENDING')

    def test_historical_pc_reward_does_not_rescue_low_fitness(self):
        for historical in (
            stats(2.03, 0.45, 0.00175, 2.0, 0.2),
            stats(2.54, 0.48, 0.00121, 2.0, 0.2),
        ):
            historical.update(pc=0.0, sc=0.0, passed=True)
            result = evaluate_stage_candidate(historical, 1)
            self.assertFalse(result['eligible'])
            self.assertIn('fitness<=0.5', result['gate']['failed'])

    def test_complete_hard_gate_candidate_outranks_high_score_gate_failure(self):
        failed = stats(sharpe=3.0, fitness=2.0, margin=0.01, turnover=0.9)
        passed = stats(sharpe=1.7, fitness=1.1, margin=0.0011, turnover=0.2)
        self.assertTrue(is_candidate_better(passed, 50.0, failed, 99.0, stage=3))

    def test_missing_metric_is_pending_and_never_formats_as_score(self):
        missing = stats()
        missing['sharpe'] = None
        result = evaluate_stage_candidate(missing, 1)
        self.assertEqual(result['status'], 'PENDING')
        self.assertIsNone(result['score'])
        self.assertIn('sharpe', result['gate']['missing'])

    def test_known_hard_failure_dominates_later_missing_metric(self):
        candidate = stats(sharpe=0.8, sc=None)
        gate = evaluate_stage_gate(candidate, 1)
        self.assertEqual(gate['status'], 'FAIL')
        self.assertIn('sharpe<=1.2', gate['failed'])
        self.assertIn('sc', gate['missing'])

    def test_stage_three_unknown_platform_check_is_pending_not_failed(self):
        candidate = stats(passed=None)
        gate = evaluate_stage_gate(candidate, 3)
        self.assertEqual(gate['status'], 'PENDING')
        self.assertIn('platform_checks', gate['missing'])

    def test_margin_repair_readiness_uses_current_stage_non_margin_gates(self):
        for stage, candidate in (
            (1, stats(1.3, 0.6, 0.0002, 1.1, 0.2, False, None)),
            (2, stats(1.5, 0.8, 0.0005, 1.4, 0.2, False, None)),
            (3, stats(1.7, 1.1, 0.0009, 1.7, 0.2, False, None)),
        ):
            readiness = evaluate_margin_repair_readiness(candidate, stage)
            self.assertTrue(readiness['ready'])
            self.assertTrue(readiness['non_margin_passed'])

    def test_margin_repair_rejects_other_failure_or_already_passing_margin(self):
        self.assertFalse(evaluate_margin_repair_readiness(
            stats(sharpe=1.1, margin=0.0002, sc=None), 1
        )['ready'])
        self.assertFalse(evaluate_margin_repair_readiness(
            stats(margin=0.0004, sc=None), 1
        )['ready'])
        self.assertFalse(evaluate_margin_repair_readiness(
            stats(margin=0.0002, turnover=0.01, sc=None), 1
        )['ready'])

    def test_margin_repair_rank_rejects_high_margin_with_invalid_turnover(self):
        safe = stats(1.7, 1.1, 0.0011, 1.7, 0.2, False, None)
        unsafe = stats(2.5, 2.0, 0.01, 2.5, 0.01, False, None)
        self.assertGreater(margin_repair_rank_key(safe, 3), margin_repair_rank_key(unsafe, 3))


if __name__ == '__main__':
    unittest.main()
