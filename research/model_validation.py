"""Validate the expected QBER model against the existing BB84 simulator.

Run this module from the repository root:

    python -m research.model_validation

The output contains one row per simulation trial so that later statistical
analyses do not depend only on pre-aggregated means.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd


Simulator = Callable[..., dict]


def expected_qber_exact(actual_noise: float, eve_interception: float) -> float:
    """Expected QBER for the bit-flip and partial intercept-resend model.

    q(b, p) = b + p * (1/4 - b/2)
    """
    _validate_probability("actual_noise", actual_noise)
    _validate_probability("eve_interception", eve_interception)
    return actual_noise + eve_interception * (0.25 - actual_noise / 2.0)


def expected_qber_additive(actual_noise: float, eve_interception: float) -> float:
    """Common additive approximation: q(b, p) = b + p/4."""
    _validate_probability("actual_noise", actual_noise)
    _validate_probability("eve_interception", eve_interception)
    return actual_noise + eve_interception * 0.25


def run_model_validation_experiment(
    *,
    actual_noise_rates: Iterable[float] = (0.00, 0.01, 0.03, 0.05),
    eve_interception_rates: Iterable[float] = (0.00, 0.10, 0.20),
    raw_qubits: int = 5000,
    trials_per_combination: int = 200,
    seed: int = 2026,
    simulator: Simulator | None = None,
) -> pd.DataFrame:
    """Run every noise/interception combination and retain trial-level data.

    A separate random seed is recorded for every trial. This makes an
    individual surprising result reproducible without rerunning the full grid.
    """
    if raw_qubits <= 0:
        raise ValueError("raw_qubits must be positive.")
    if trials_per_combination <= 0:
        raise ValueError("trials_per_combination must be positive.")

    noise_rates = [float(value) for value in actual_noise_rates]
    interception_rates = [float(value) for value in eve_interception_rates]
    for value in noise_rates:
        _validate_probability("actual_noise", value)
    for value in interception_rates:
        _validate_probability("eve_interception", value)

    if simulator is None:
        from src.bb84 import run_bb84_with_eve

        simulator = run_bb84_with_eve

    seed_generator = np.random.default_rng(seed)
    rows: list[dict] = []
    trial_id = 0

    for actual_noise in noise_rates:
        for eve_interception in interception_rates:
            exact_qber = expected_qber_exact(actual_noise, eve_interception)
            additive_qber = expected_qber_additive(
                actual_noise, eve_interception
            )

            for condition_trial in range(trials_per_combination):
                trial_seed = int(
                    seed_generator.integers(0, np.iinfo(np.uint32).max)
                )

                # The existing simulator uses NumPy's global random functions.
                # Seeding here makes each individual trial reproducible.
                np.random.seed(trial_seed)
                result = simulator(
                    n=raw_qubits,
                    eve_intercept_prob=eve_interception,
                    channel_noise_prob=actual_noise,
                )

                alice_key = np.asarray(result["alice_key"])
                bob_key = np.asarray(result["bob_key"])
                if len(alice_key) != len(bob_key):
                    raise RuntimeError("Alice and Bob sifted keys differ in length.")

                error_count = int(np.count_nonzero(alice_key != bob_key))
                sifted_bits = int(len(alice_key))
                measured_qber = (
                    error_count / sifted_bits if sifted_bits > 0 else np.nan
                )

                rows.append(
                    {
                        "trial_id": trial_id,
                        "condition_trial": condition_trial,
                        "master_seed": seed,
                        "trial_seed": trial_seed,
                        "raw_qubits": raw_qubits,
                        "sifted_bits": sifted_bits,
                        "error_count": error_count,
                        "measured_qber": measured_qber,
                        "actual_noise": actual_noise,
                        "eve_interception": eve_interception,
                        "expected_qber_exact": exact_qber,
                        "expected_qber_additive": additive_qber,
                    }
                )
                trial_id += 1

    return pd.DataFrame(rows)


def summarize_model_validation(trials: pd.DataFrame) -> pd.DataFrame:
    """Create one summary row per experimental condition."""
    required = {
        "actual_noise",
        "eve_interception",
        "measured_qber",
        "sifted_bits",
        "expected_qber_exact",
        "expected_qber_additive",
    }
    missing = required.difference(trials.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    summary = (
        trials.groupby(["actual_noise", "eve_interception"], as_index=False)
        .agg(
            trials=("measured_qber", "size"),
            mean_sifted_bits=("sifted_bits", "mean"),
            mean_measured_qber=("measured_qber", "mean"),
            sd_measured_qber=("measured_qber", "std"),
            expected_qber_exact=("expected_qber_exact", "first"),
            expected_qber_additive=("expected_qber_additive", "first"),
        )
        .sort_values(["actual_noise", "eve_interception"])
        .reset_index(drop=True)
    )
    summary["absolute_error_exact"] = (
        summary["mean_measured_qber"] - summary["expected_qber_exact"]
    ).abs()
    summary["absolute_error_additive"] = (
        summary["mean_measured_qber"] - summary["expected_qber_additive"]
    ).abs()
    return summary


def save_results(
    trials: pd.DataFrame,
    *,
    output_directory: str | Path = "research/results/model_validation",
) -> tuple[Path, Path]:
    """Save trial-level and summary CSV files."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    trials_path = output_path / "model_validation_trials.csv"
    summary_path = output_path / "model_validation_summary.csv"
    trials.to_csv(trials_path, index=False)
    summarize_model_validation(trials).to_csv(summary_path, index=False)
    return trials_path, summary_path


def _validate_probability(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-qubits", type=int, default=5000)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output-directory",
        default="research/results/model_validation",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    trials = run_model_validation_experiment(
        raw_qubits=args.raw_qubits,
        trials_per_combination=args.trials,
        seed=args.seed,
    )
    trials_path, summary_path = save_results(
        trials, output_directory=args.output_directory
    )
    print(f"Saved {len(trials)} trial rows to {trials_path}")
    print(f"Saved condition summary to {summary_path}")
    print(summarize_model_validation(trials).to_string(index=False))


if __name__ == "__main__":
    main()

