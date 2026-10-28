"""Tests for finite-horizon exact two-sample QBER monitoring."""

import unittest

from scipy.stats import binom

from research.two_sample_monitoring_study import (
    BASELINE_QBER,
    CALIBRATION_BITS,
    FAMILYWISE_ALPHA,
    INTERCEPTION_DENSITY,
    OPERATING_BLOCKS,
    SIFTED_LENGTH,
    build_scenarios,
    critical_count,
    evaluate_study,
    exact_two_sample_critical_count,
    exact_two_sample_pvalue,
    expected_qber,
)


class ExactTwoSampleTests(unittest.TestCase):
    def test_pvalue_lies_in_unit_interval(self):
        value = exact_two_sample_pvalue(150, 5000, 50, 1000)
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_more_operating_errors_give_stronger_evidence(self):
        low = exact_two_sample_pvalue(150, 5000, 40, 1000)
        high = exact_two_sample_pvalue(150, 5000, 60, 1000)
        self.assertLess(high, low)

    def test_critical_count_is_minimal(self):
        alpha = FAMILYWISE_ALPHA / OPERATING_BLOCKS
        threshold = exact_two_sample_critical_count(
            150, CALIBRATION_BITS, SIFTED_LENGTH, alpha
        )
        self.assertLessEqual(
            exact_two_sample_pvalue(
                150, CALIBRATION_BITS, threshold, SIFTED_LENGTH
            ),
            alpha,
        )
        self.assertGreater(
            exact_two_sample_pvalue(
                150, CALIBRATION_BITS, threshold - 1, SIFTED_LENGTH
            ),
            alpha,
        )


class FiniteHorizonTests(unittest.TestCase):
    def test_oracle_threshold_respects_per_block_allocation(self):
        alpha = FAMILYWISE_ALPHA / OPERATING_BLOCKS
        threshold = critical_count(SIFTED_LENGTH, BASELINE_QBER, alpha)
        self.assertLessEqual(
            binom.sf(threshold - 1, SIFTED_LENGTH, BASELINE_QBER),
            alpha,
        )

    def test_all_stationary_run_probabilities_respect_familywise_target(self):
        frame, _ = evaluate_study()
        stationary = frame[frame["scenario_id"] == "stationary"]
        self.assertTrue(
            (stationary["run_alert_probability"] <= FAMILYWISE_ALPHA).all()
        )

    def test_cp_allocation_has_one_percent_upper_bound(self):
        frame, _ = evaluate_study()
        cp = frame[frame["method"] == "Clopper-Pearson margin"]
        self.assertTrue(
            (cp["familywise_upper_bound"] == FAMILYWISE_ALPHA).all()
        )


class IdentifiabilityTests(unittest.TestCase):
    def test_matched_benign_and_attack_qber_paths_are_identical(self):
        scenarios = {scenario.scenario_id: scenario for scenario in build_scenarios()}
        self.assertEqual(
            scenarios["matched_benign_step"].qber_path,
            scenarios["intercept_resend"].qber_path,
        )
        self.assertAlmostEqual(
            scenarios["intercept_resend"].qber_path[0],
            expected_qber(BASELINE_QBER, INTERCEPTION_DENSITY),
        )

    def test_every_method_has_identical_probability_for_matched_causes(self):
        frame, _ = evaluate_study()
        benign = frame[frame["scenario_id"] == "matched_benign_step"].set_index(
            "method"
        )
        attack = frame[frame["scenario_id"] == "intercept_resend"].set_index(
            "method"
        )
        for method in benign.index:
            self.assertAlmostEqual(
                benign.loc[method, "run_alert_probability"],
                attack.loc[method, "run_alert_probability"],
                places=14,
            )


if __name__ == "__main__":
    unittest.main()
