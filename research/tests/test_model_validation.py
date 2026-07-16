import unittest

import numpy as np

from research.model_validation import (
    expected_qber_additive,
    expected_qber_exact,
    run_model_validation_experiment,
    summarize_model_validation,
)


class ModelEquationTests(unittest.TestCase):
    def test_exact_model_boundary_cases(self):
        self.assertAlmostEqual(expected_qber_exact(0.03, 0.0), 0.03)
        self.assertAlmostEqual(expected_qber_exact(0.0, 1.0), 0.25)
        self.assertAlmostEqual(expected_qber_exact(0.03, 0.10), 0.0535)

    def test_additive_difference(self):
        exact = expected_qber_exact(0.03, 0.10)
        additive = expected_qber_additive(0.03, 0.10)
        self.assertAlmostEqual(additive - exact, 0.0015)

    def test_invalid_probability(self):
        with self.assertRaises(ValueError):
            expected_qber_exact(-0.01, 0.10)


class ExperimentTests(unittest.TestCase):
    @staticmethod
    def fake_simulator(n, eve_intercept_prob, channel_noise_prob):
        sifted_bits = n // 2
        qber = expected_qber_exact(channel_noise_prob, eve_intercept_prob)
        errors = int(round(sifted_bits * qber))
        alice_key = np.zeros(sifted_bits, dtype=int)
        bob_key = alice_key.copy()
        bob_key[:errors] = 1
        return {"alice_key": alice_key, "bob_key": bob_key}

    def test_trial_rows_and_summary(self):
        trials = run_model_validation_experiment(
            actual_noise_rates=[0.0, 0.03],
            eve_interception_rates=[0.0, 0.10],
            raw_qubits=1000,
            trials_per_combination=3,
            seed=2026,
            simulator=self.fake_simulator,
        )
        self.assertEqual(len(trials), 12)
        self.assertEqual(trials["trial_seed"].nunique(), 12)
        self.assertTrue(
            {"sifted_bits", "error_count", "measured_qber"}.issubset(
                trials.columns
            )
        )

        summary = summarize_model_validation(trials)
        self.assertEqual(len(summary), 4)
        self.assertTrue((summary["absolute_error_exact"] <= 0.001).all())


if __name__ == "__main__":
    unittest.main()

