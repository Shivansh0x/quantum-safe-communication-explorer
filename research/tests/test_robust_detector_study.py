import unittest

import numpy as np

from research.robust_detector_study import (
    RobustDetectorConfig,
    run_robust_detector_study,
)


class RobustDetectorTests(unittest.TestCase):
    def setUp(self):
        self.config = RobustDetectorConfig(
            assumed_baseline=0.03,
            uncertainty_margins=(0.0, 0.01, 0.02),
            actual_baselines=(0.02, 0.03, 0.04, 0.05),
            eve_interceptions=(0.0, 0.05, 0.10),
            sifted_lengths=(500, 1000),
            alpha=0.01,
            trials_per_condition=1000,
            master_seed=2027,
        )
        self.summary = run_robust_detector_study(self.config)

    def test_grid_size_and_unique_seeds(self):
        expected = 3 * 4 * 3 * 2
        self.assertEqual(len(self.summary), expected)
        self.assertEqual(self.summary["condition_seed"].nunique(), expected)

    def test_fpr_control_within_declared_bound(self):
        rows = self.summary[
            np.isclose(self.summary["eve_interception"], 0.0)
            & self.summary["baseline_within_declared_bound"]
        ]
        self.assertTrue(
            (rows["theoretical_alarm_rate"] <= self.config.alpha + 1e-15).all()
        )

    def test_larger_margin_does_not_increase_alarm_probability(self):
        for _, group in self.summary.groupby(
            ["sifted_length", "actual_baseline", "eve_interception"]
        ):
            ordered = group.sort_values("uncertainty_margin")
            rates = ordered["theoretical_alarm_rate"].to_numpy()
            self.assertTrue(np.all(np.diff(rates) <= 1e-15))


if __name__ == "__main__":
    unittest.main()

