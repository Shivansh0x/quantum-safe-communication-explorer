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