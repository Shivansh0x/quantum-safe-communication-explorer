"""Tests for the data-driven uncertainty margin experiment."""

import unittest

from scipy.stats import binom

from research.calibration_budget_study import (
    clopper_pearson_upper,
    critical_count,
    expected_qber,
    wilson_interval,
)


class TestClopperPearsonUpper(unittest.TestCase):
    def test_upper_bound_exceeds_point_estimate(self):
        self.assertGreater(clopper_pearson_upper(30, 1000, 0.01), 0.03)

    def test_bound_tightens_with_more_data(self):
        small = clopper_pearson_upper(30, 1000, 0.01)
        large = clopper_pearson_upper(3000, 100_000, 0.01)
        self.assertLess(large, small)

    def test_bound_widens_as_level_tightens(self):
        loose = clopper_pearson_upper(150, 5000, 0.01)
        tight = clopper_pearson_upper(150, 5000, 0.001)
        self.assertGreater(tight, loose)

    def test_saturated_case_returns_one(self):
        self.assertEqual(clopper_pearson_upper(100, 100, 0.01), 1.0)

    def test_rejects_out_of_range_errors(self):
        with self.assertRaises(ValueError):
            clopper_pearson_upper(101, 100, 0.01)


class TestCriticalCount(unittest.TestCase):
    def test_matches_published_fixed_threshold(self):
        self.assertEqual(critical_count(1000, 0.03, 0.01), 44)

    def test_threshold_is_minimal(self):
        threshold = critical_count(1000, 0.03, 0.01)
        self.assertLessEqual(binom.sf(threshold - 1, 1000, 0.03), 0.01)
        self.assertGreater(binom.sf(threshold - 2, 1000, 0.03), 0.01)

    def test_threshold_is_nondecreasing_in_baseline(self):
        low = critical_count(1000, 0.03, 0.01)
        high = critical_count(1000, 0.04, 0.01)
        self.assertGreaterEqual(high, low)

    def test_conditional_guarantee_holds_within_bound(self):
        # Equation (6): any actual baseline at or below the calibration
        # baseline must respect the target level.
        threshold = critical_count(1000, 0.04, 0.01)
        for actual in (0.005, 0.02, 0.03, 0.04):
            self.assertLessEqual(binom.sf(threshold - 1, 1000, actual), 0.01)


class TestExpectedQber(unittest.TestCase):
    def test_no_attack_reduces_to_baseline(self):
        self.assertAlmostEqual(expected_qber(0.03, 0.0), 0.03)

    def test_noiseless_full_interception_gives_quarter(self):
        self.assertAlmostEqual(expected_qber(0.0, 1.0), 0.25)

    def test_stays_below_additive_approximation(self):
        exact = expected_qber(0.05, 0.20)
        additive = 0.05 + 0.20 / 4.0
        self.assertLess(exact, additive)
        self.assertAlmostEqual(additive - exact, 0.05 * 0.20 / 2.0)

    def test_rejects_invalid_interception_density(self):
        with self.assertRaises(ValueError):
            expected_qber(0.03, 1.5)


class TestWilsonInterval(unittest.TestCase):
    def test_interval_contains_point_estimate(self):
        low, high = wilson_interval(500, 10_000)
        self.assertLess(low, 0.05)
        self.assertGreater(high, 0.05)

    def test_endpoints_stay_in_unit_interval(self):
        low, high = wilson_interval(0, 100)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)


if __name__ == "__main__":
    unittest.main()
