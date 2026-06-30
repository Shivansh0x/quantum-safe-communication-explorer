import numpy as np
import pandas as pd

from bb84 import run_bb84_with_eve
from error_correction import parity_error_correction


def run_error_correction_parameter_sweep(
    n: int = 8000,
    trials_per_setting: int = 20,
    block_sizes=None,
    pass_counts=None,
    eve_intercept_prob: float = 0.05,
    channel_noise_prob: float = 0.02,
    seed: int = 42
) -> pd.DataFrame:
    """
    Run a parameter sweep for parity-based error correction.

    The experiment varies:
    - block size
    - number of correction passes

    For each setting, the function records:
    - correction success rate
    - average raw mismatches
    - average final mismatches
    - average corrections applied
    - average parity checks
    - average QBER
    """

    if block_sizes is None:
        block_sizes = [8, 16, 32, 64]

    if pass_counts is None:
        pass_counts = [1, 3, 5, 7, 10]

    rows = []

    for block_size in block_sizes:
        for passes in pass_counts:
            success_values = []
            qber_values = []
            raw_mismatch_values = []
            final_mismatch_values = []
            corrections_values = []
            parity_check_values = []
            raw_key_lengths = []

            for trial in range(trials_per_setting):
                bb84_result = run_bb84_with_eve(
                    n=n,
                    eve_intercept_prob=eve_intercept_prob,
                    channel_noise_prob=channel_noise_prob
                )

                alice_key = bb84_result["alice_key"]
                bob_key = bb84_result["bob_key"]

                correction_result = parity_error_correction(
                    alice_key,
                    bob_key,
                    block_size=block_size,
                    passes=passes,
                    seed=seed + trial
                )

                success_values.append(int(correction_result["success"]))
                qber_values.append(bb84_result["qber"])
                raw_mismatch_values.append(correction_result["raw_mismatches"])
                final_mismatch_values.append(correction_result["final_mismatches"])
                corrections_values.append(correction_result["corrections_applied"])
                parity_check_values.append(correction_result["parity_checks"])
                raw_key_lengths.append(len(alice_key))

            rows.append({
                "block_size": block_size,
                "passes": passes,
                "eve_intercept_prob": eve_intercept_prob,
                "channel_noise_prob": channel_noise_prob,
                "trials_per_setting": trials_per_setting,
                "qubits_per_trial": n,
                "success_rate": float(np.mean(success_values)),
                "average_qber": float(np.mean(qber_values)),
                "average_raw_key_length": float(np.mean(raw_key_lengths)),
                "average_raw_mismatches": float(np.mean(raw_mismatch_values)),
                "average_final_mismatches": float(np.mean(final_mismatch_values)),
                "average_corrections_applied": float(np.mean(corrections_values)),
                "average_parity_checks": float(np.mean(parity_check_values))
            })

    return pd.DataFrame(rows)