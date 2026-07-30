import unittest

import numpy as np
from scipy.stats import binom

from research.detector_study import (
    DetectorStudyConfig,
    critical_error_count,
    run_detector_study,
    theoretical_detection_probability,
    wilson_interval,
)


class ThresholdTests(unittest.TestCase):
    def test_critical_count_is_minimal(self):
        k = 1000
        baseline = 0.03
        alpha = 0.01
        critical = critical_error_count(
            sifted_length=k, assumed_baseline=baseline, alpha=alpha
        )
        self.assertLessEqual(float(binom.sf(critical - 1, k, baseline)), alpha)
        self.assertGreater(float(binom.sf(critical - 2, k, baseline)), alpha)

    def test_detection_probability(self):
        probability = theoretical_detection_probability(
            error_probability=0.03,
            sifted_length=1000,
            critical_count=45,
        )
        self.assertAlmostEqual(probability, float(binom.sf(44, 1000, 0.03)))

    def test_wilson_interval_contains_estimate(self):
        low, high = wilson_interval(10, 100)
        self.assertLess(low, 0.10)
        self.assertGreater(high, 0.10)


class StudyTests(unittest.TestCase):
    def test_small_study_grid(self):
        config = DetectorStudyConfig(
            assumed_baseline=0.03,
            actual_baselines=(0.02, 0.03, 0.04),
            eve_interceptions=(0.0, 0.10),
            sifted_lengths=(500, 1000),
            alpha=0.01,
            trials_per_condition=2000,
            master_seed=2026,
        )
        summary = run_detector_study(config)
        self.assertEqual(len(summary), 12)
        self.assertEqual(summary["condition_seed"].nunique(), 12)

        no_eve = summary[np.isclose(summary["eve_interception"], 0.0)]
        for _, group in no_eve.groupby("sifted_length"):
            ordered = group.sort_values("actual_baseline")
            rates = ordered["theoretical_detection_rate"].to_numpy()
            self.assertTrue(np.all(np.diff(rates) >= 0.0))

        calibrated = summary[
            np.isclose(summary["actual_baseline"], 0.03)
            & np.isclose(summary["eve_interception"], 0.0)
        ]
        self.assertTrue(
            (calibrated["calibrated_fpr_theoretical"] <= config.alpha).all()
        )


if __name__ == "__main__":
    unittest.main()

