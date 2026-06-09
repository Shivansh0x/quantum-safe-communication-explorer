import numpy as np
import pandas as pd

from bb84 import run_bb84_with_eve

def run_qber_experiment(n=5000, interception_rates=None, trials_per_rate=20):
    """
    Run BB84 with Eve across multiple interception probabilities.

    For each interception rate, the simulation is repeated multiple times.
    The function returns the average QBER and standard deviation for each rate.

    Expected theory:
    For a simple intercept-resend attack in BB84,

        expected QBER ≈ Eve interception probability x 0.25

    because:
    - Eve chooses the wrong basis about 50% of the time.
    - When Eve chooses the wrong basis, Bob gets the wrong bit about 50% of the time.
    - Therefore, the error rate from intercepted qubits is about 0.5 x 0.5 = 0.25.
    """
    if interception_rates is None:
        interception_rates=np.linspace(0, 1, 11)
    
    experiment_rows = []

    for rate in interception_rates:
        qber_values = []

        for _ in range(trials_per_rate):
            result = run_bb84_with_eve(n=n, eve_intercept_prob=float(rate))
            qber_values.append(result["qber"])
        
        avg_qber = np.mean(qber_values)
        std_qber = np.std(qber_values)
        expected_qber = float(rate) * 0.25

        experiment_rows.append({
                "eve_interception_rate": float(rate),
                "average_qber": avg_qber,
                "std_qber": std_qber,
                "expected_qber": expected_qber,
                "trials_per_rate": trials_per_rate,
                "qubits_per_trial": n
        })

    return pd.DataFrame(experiment_rows)

def run_channel_noise_experiment(n=5000, noise_probabilities=None, trials_per_rate=20, eve_intercept_prob=0.0):
    """
    Run BB84 across multiple channel noise probabilities.

    This experiment measures how QBER changes when the channel itself
    introduces bit-flip noise, even when Eve is absent or fixed at a chosen level.
    """

    if noise_probabilities is None:
        noise_probabilities = np.linspace(0, 0.20, 11)

    experiment_rows = []

    for noise_prob in noise_probabilities:
        qber_values = []

        for _ in range(trials_per_rate):
            result = run_bb84_with_eve(
                n=n,
                eve_intercept_prob=eve_intercept_prob,
                channel_noise_prob=float(noise_prob)
            )

            qber_values.append(result["qber"])

        avg_qber = np.mean(qber_values)
        std_qber = np.std(qber_values)

        experiment_rows.append({
            "channel_noise_probability": float(noise_prob),
            "eve_interception_rate": float(eve_intercept_prob),
            "average_qber": avg_qber,
            "std_qber": std_qber,
            "trials_per_rate": trials_per_rate,
            "qubits_per_trial": n
        })

    return pd.DataFrame(experiment_rows)

def run_eve_noise_comparison_experiment(n = 5000, trials_per_scenario= 20, eve_intercept_prob = 0.10, 
                                        channel_noise_prob = 0.03):
    """
    Compare QBER across four BB84 communication scenarios:

    1. Clean channel: no Eve, no noise
    2. Noise only: no Eve, channel noise present
    3. Eve only: Eve present, no channel noise
    4. Eve + noise: both Eve and channel noise present

    This helps separate errors caused by eavesdropping from errors caused
    by ordinary channel noise.
    """

    scenarios = [
        {
            "scenario": "Clean channel",
            "eve_interception_rate": 0.0,
            "channel_noise_probability": 0.0
        },
        {
            "scenario": "Noise only",
            "eve_interception_rate": 0.0,
            "channel_noise_probability": channel_noise_prob
        },
        {
            "scenario": "Eve only",
            "eve_interception_rate": eve_intercept_prob,
            "channel_noise_probability": 0.0
        },
        {
            "scenario": "Eve + noise",
            "eve_interception_rate": eve_intercept_prob,
            "channel_noise_probability": channel_noise_prob
        }
    ]

    experiment_rows = []

    for scenario in scenarios:
        qber_values = []

        for _ in range(trials_per_scenario):
            result = run_bb84_with_eve(
                n=n,
                eve_intercept_prob=scenario["eve_interception_rate"],
                channel_noise_prob=scenario["channel_noise_probability"]
            )

            qber_values.append(result["qber"])

        avg_qber = np.mean(qber_values)
        std_qber = np.std(qber_values)

        experiment_rows.append({
            "scenario": scenario["scenario"],
            "eve_interception_rate": scenario["eve_interception_rate"],
            "channel_noise_probability": scenario["channel_noise_probability"],
            "average_qber": avg_qber,
            "std_qber": std_qber,
            "trials_per_scenario": trials_per_scenario,
            "qubits_per_trial": n
        })

    return pd.DataFrame(experiment_rows)