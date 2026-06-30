import numpy as np
import pandas as pd

from encryption import run_secure_message_exchange, message_to_bits


def make_test_message(length_chars: int) -> str:
    """
    Create a simple test message of a selected character length.
    """
    return "Q" * length_chars


def run_privacy_amplification_parameter_sweep(
    n: int = 10000,
    trials_per_setting: int = 10,
    compression_ratios=None,
    message_lengths_chars=None,
    eve_intercept_prob: float = 0.03,
    channel_noise_prob: float = 0.01,
    qber_threshold: float = 0.11,
    error_correction_block_size: int = 16,
    error_correction_passes: int = 10
) -> pd.DataFrame:
    """
    Run a parameter sweep for privacy amplification.

    The experiment varies:
    - privacy compression ratio
    - message length

    For each setting, it records:
    - success rate
    - average reconciled key length
    - average final key capacity
    - message bits required
    - number of insufficient-key failures
    """

    if compression_ratios is None:
        compression_ratios = [0.25, 0.40, 0.50, 0.75, 0.90]

    if message_lengths_chars is None:
        message_lengths_chars = [16, 64, 128, 256]

    rows = []

    for message_length_chars in message_lengths_chars:
        message = make_test_message(message_length_chars)
        message_bits_required = len(message_to_bits(message))

        for compression_ratio in compression_ratios:
            success_values = []
            qber_values = []
            reconciled_key_lengths = []
            final_key_capacities = []
            insufficient_key_failures = 0
            mismatch_failures = 0
            qber_failures = 0

            for _ in range(trials_per_setting):
                result = run_secure_message_exchange(
                    message=message,
                    n_qubits=n,
                    eve_intercept_prob=eve_intercept_prob,
                    channel_noise_prob=channel_noise_prob,
                    qber_threshold=qber_threshold,
                    use_error_correction=True,
                    error_correction_block_size=error_correction_block_size,
                    error_correction_passes=error_correction_passes,
                    use_privacy_amplification=True,
                    privacy_compression_ratio=compression_ratio
                )

                success = result["status"] == "success"
                success_values.append(int(success))
                qber_values.append(result["qber"])

                reconciled_key_length = result.get("reconciled_key_length", 0)
                reconciled_key_lengths.append(reconciled_key_length)

                final_key_capacity = int(reconciled_key_length * compression_ratio)
                final_key_capacities.append(final_key_capacity)

                reason = result.get("reason", "")

                if "Not enough reconciled key material" in reason:
                    insufficient_key_failures += 1

                if "keys still do not match" in reason or "Final derived keys do not match" in reason:
                    mismatch_failures += 1

                if "QBER exceeded threshold" in reason:
                    qber_failures += 1

            rows.append({
                "message_length_chars": message_length_chars,
                "message_bits_required": message_bits_required,
                "privacy_compression_ratio": float(compression_ratio),
                "eve_intercept_prob": eve_intercept_prob,
                "channel_noise_prob": channel_noise_prob,
                "qber_threshold": qber_threshold,
                "trials_per_setting": trials_per_setting,
                "qubits_per_trial": n,
                "success_rate": float(np.mean(success_values)),
                "average_qber": float(np.mean(qber_values)),
                "average_reconciled_key_length": float(np.mean(reconciled_key_lengths)),
                "average_final_key_capacity": float(np.mean(final_key_capacities)),
                "insufficient_key_failures": insufficient_key_failures,
                "mismatch_failures": mismatch_failures,
                "qber_failures": qber_failures
            })

    return pd.DataFrame(rows)