import unittest

import numpy as np

from research.full_bb84_validation import (
    FullBB84ValidationConfig,
    run_fixed_sifted_bb84_trial,
    run_full_bb84_validation,
)


class FullBB84ValidationTests(unittest.TestCase):
    @staticmethod
    def fake_simulator(n, eve_intercept_prob, channel_noise_prob):
        sifted = max(1, n // 2)
        qber = channel_noise_prob + eve_intercept_prob * (
            0.25 - channel_noise_prob / 2.0
        )
        errors = int(round(sifted * qber))
        alice = np.zeros(sifted, dtype=int)
        bob = alice.copy()
        # Spread deterministic errors across the batch so taking exactly K
        # sifted bits does not artificially concentrate every error at the
        # beginning of the returned key.
        if errors:
            error_positions = np.linspace(0, sifted - 1, errors, dtype=int)
            bob[error_positions] = 1
        return {"alice_key": alice, "bob_key": bob}

    def test_exact_sifted_length(self):
        result = run_fixed_sifted_bb84_trial(
            sifted_length=1000,
            actual_baseline=0.03,
            eve_interception=0.10,
            seed=2028,
            simulator=self.fake_simulator,
        )
        self.assertEqual(result["sifted_bits"], 1000)
        expected = 0.03 + 0.10 * (0.25 - 0.03 / 2.0)
        self.assertLess(abs(result["measured_qber"] - expected), 0.002)

    def test_small_grid(self):
        config = FullBB84ValidationConfig(
            actual_baselines=(0.01, 0.03),
            eve_interceptions=(0.0, 0.10),
            sifted_lengths=(250, 1000),
            trials_per_condition=3,
            master_seed=2028,
        )
        trials, summary = run_full_bb84_validation(
            config, simulator=self.fake_simulator
        )
        self.assertEqual(len(trials), 24)
        self.assertEqual(len(summary), 8)
        self.assertEqual(trials["trial_seed"].nunique(), 24)
        self.assertTrue((trials["sifted_bits"] == trials["sifted_length"]).all())


if __name__ == "__main__":
    unittest.main()
