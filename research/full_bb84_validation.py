"""Cross-validate the statistical detector study with the bit-level BB84 code.

The main detector grids use Binomial(K, q), which is exact under the validated
iid model. This module runs selected conditions through src.bb84 and collects
exactly K sifted bits per trial, allowing a direct comparison of mean QBER and
alarm probabilities.

Run from the repository root:

    python -m research.full_bb84_validation
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from research.detector_study import (
    critical_error_count,
    theoretical_detection_probability,
    wilson_interval,
)
from research.model_validation import expected_qber_exact


Simulator = Callable[..., dict]
SCRIPT_VERSION = "1.0.1"


@dataclass(frozen=True)
class FullBB84ValidationConfig:
    assumed_baseline: float = 0.03
    actual_baselines: tuple[float, ...] = (0.01, 0.03, 0.05)
    eve_interceptions: tuple[float, ...] = (0.00, 0.05, 0.10, 0.20)
    sifted_lengths: tuple[int, ...] = (250, 1000, 5000)
    alpha: float = 0.01
    trials_per_condition: int = 200
    master_seed: int = 2028

    def validate(self) -> None:
        for name, value in (
            ("assumed_baseline", self.assumed_baseline),
            ("alpha", self.alpha),
        ):
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must lie in (0, 1].")
        for value in self.actual_baselines + self.eve_interceptions:
            if not 0.0 <= value <= 1.0:
                raise ValueError("All probabilities must lie in [0, 1].")
        if any(length <= 0 for length in self.sifted_lengths):
            raise ValueError("Sifted lengths must be positive.")
        if self.trials_per_condition <= 0:
            raise ValueError("trials_per_condition must be positive.")


def run_fixed_sifted_bb84_trial(
    *,
    sifted_length: int,
    actual_baseline: float,
    eve_interception: float,
    seed: int,
    simulator: Simulator | None = None,
) -> dict:
    """Collect exactly K sifted bits from one or more simulator batches."""
    if sifted_length <= 0:
        raise ValueError("sifted_length must be positive.")
    if simulator is None:
        from src.bb84 import run_bb84_with_eve

        simulator = run_bb84_with_eve

    np.random.seed(seed % (np.iinfo(np.uint32).max + 1))
    remaining = sifted_length
    total_errors = 0
    total_raw_qubits = 0
    batches = 0

    while remaining > 0:
        # Basis matching retains about half of transmitted qubits. The 10%
        # cushion usually completes a trial in one call but the loop is exact.
        raw_batch = max(200, int(np.ceil(2.2 * remaining)))
        result = simulator(
            n=raw_batch,
            eve_intercept_prob=eve_interception,
            channel_noise_prob=actual_baseline,
        )
        alice_key = np.asarray(result["alice_key"])
        bob_key = np.asarray(result["bob_key"])
        if len(alice_key) != len(bob_key):
            raise RuntimeError("Alice and Bob sifted keys differ in length.")
        take = min(remaining, len(alice_key))
        if take > 0:
            total_errors += int(
                np.count_nonzero(alice_key[:take] != bob_key[:take])
            )
            remaining -= take
        total_raw_qubits += raw_batch
        batches += 1
        if batches > 100:
            raise RuntimeError("Unable to collect the requested sifted bits.")

    return {
        "sifted_bits": sifted_length,
        "error_count": total_errors,
        "measured_qber": total_errors / sifted_length,
        "raw_qubits_generated": total_raw_qubits,
        "simulator_batches": batches,
    }


def run_full_bb84_validation(
    config: FullBB84ValidationConfig,
    *,
    simulator: Simulator | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    config.validate()
    rows: list[dict] = []

    for sifted_length in config.sifted_lengths:
        critical_count = critical_error_count(
            sifted_length=sifted_length,
            assumed_baseline=config.assumed_baseline,
            alpha=config.alpha,
        )
        for actual_baseline in config.actual_baselines:
            for eve_interception in config.eve_interceptions:
                expected_qber = expected_qber_exact(
                    actual_baseline, eve_interception
                )
                theoretical_alarm_rate = theoretical_detection_probability(
                    error_probability=expected_qber,
                    sifted_length=sifted_length,
                    critical_count=critical_count,
                )
                for condition_trial in range(config.trials_per_condition):
                    trial_seed = _trial_seed(
                        config.master_seed,
                        actual_baseline,
                        eve_interception,
                        sifted_length,
                        condition_trial,
                    )
                    trial = run_fixed_sifted_bb84_trial(
                        sifted_length=sifted_length,
                        actual_baseline=actual_baseline,
                        eve_interception=eve_interception,
                        seed=trial_seed,
                        simulator=simulator,
                    )
                    rows.append(
                        {
                            "script_version": SCRIPT_VERSION,
                            "master_seed": config.master_seed,
                            "trial_seed": trial_seed,
                            "condition_trial": condition_trial,
                            "sifted_length": sifted_length,
                            "assumed_baseline": config.assumed_baseline,
                            "actual_baseline": actual_baseline,
                            "baseline_mismatch": (
                                actual_baseline - config.assumed_baseline
                            ),
                            "eve_interception": eve_interception,
                            "expected_qber_exact": expected_qber,
                            "critical_error_count": critical_count,
                            "theoretical_alarm_rate": theoretical_alarm_rate,
                            "alarm": trial["error_count"] >= critical_count,
                            **trial,
                        }
                    )

    trials = pd.DataFrame(rows).sort_values(
        ["sifted_length", "actual_baseline", "eve_interception", "condition_trial"]
    ).reset_index(drop=True)
    summary = summarize_full_bb84_validation(trials)
    return trials, summary


def summarize_full_bb84_validation(trials: pd.DataFrame) -> pd.DataFrame:
    grouped_rows: list[dict] = []
    keys = ["sifted_length", "actual_baseline", "eve_interception"]
    for values, group in trials.groupby(keys, sort=True):
        sifted_length, actual_baseline, eve_interception = values
        alarm_count = int(group["alarm"].sum())
        trial_count = len(group)
        empirical_rate = alarm_count / trial_count
        ci_low, ci_high = wilson_interval(alarm_count, trial_count)
        expected_qber = float(group["expected_qber_exact"].iloc[0])
        mean_qber = float(group["measured_qber"].mean())
        sd_qber = float(group["measured_qber"].std(ddof=1))
        qber_sem = sd_qber / np.sqrt(trial_count)
        grouped_rows.append(
            {
                "sifted_length": int(sifted_length),
                "actual_baseline": float(actual_baseline),
                "baseline_mismatch": float(
                    actual_baseline - group["assumed_baseline"].iloc[0]
                ),
                "eve_interception": float(eve_interception),
                "trials": trial_count,
                "mean_raw_qubits_generated": float(
                    group["raw_qubits_generated"].mean()
                ),
                "mean_simulator_batches": float(
                    group["simulator_batches"].mean()
                ),
                "expected_qber_exact": expected_qber,
                "mean_measured_qber": mean_qber,
                "sd_measured_qber": sd_qber,
                "qber_mean_minus_theory": mean_qber - expected_qber,
                "qber_mean_z": (
                    (mean_qber - expected_qber) / qber_sem
                    if qber_sem > 0.0
                    else 0.0
                ),
                "critical_error_count": int(
                    group["critical_error_count"].iloc[0]
                ),
                "theoretical_alarm_rate": float(
                    group["theoretical_alarm_rate"].iloc[0]
                ),
                "empirical_alarm_rate": empirical_rate,
                "alarm_rate_ci_low": ci_low,
                "alarm_rate_ci_high": ci_high,
                "empirical_minus_theoretical_alarm_rate": (
                    empirical_rate
                    - float(group["theoretical_alarm_rate"].iloc[0])
                ),
            }
        )
    return pd.DataFrame(grouped_rows)


def save_validation(
    trials: pd.DataFrame,
    summary: pd.DataFrame,
    config: FullBB84ValidationConfig,
    *,
    output_directory: str | Path = "research/results/full_bb84_validation",
    figure_directory: str | Path = "research/figures/full_bb84_validation",
) -> dict[str, Path]:
    output_path = Path(output_directory)
    figure_path = Path(figure_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    figure_path.mkdir(parents=True, exist_ok=True)

    trials_path = output_path / "full_bb84_validation_trials.csv"
    summary_path = output_path / "full_bb84_validation_summary.csv"
    config_path = output_path / "full_bb84_validation_config.json"
    qber_figure = figure_path / "bb84_mean_qber_validation.png"
    alarm_figure = figure_path / "bb84_alarm_probability_validation.png"

    trials.to_csv(trials_path, index=False)
    summary.to_csv(summary_path, index=False)
    config_path.write_text(
        json.dumps(
            {
                "script_version": SCRIPT_VERSION,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "config": asdict(config),
                "purpose": (
                    "Cross-validation of exact-binomial predictions using "
                    "the original bit-level BB84 simulator and exactly K sifted bits."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _plot_qber_validation(summary, qber_figure)
    _plot_alarm_validation(summary, alarm_figure)
    return {
        "trials": trials_path,
        "summary": summary_path,
        "config": config_path,
        "qber_figure": qber_figure,
        "alarm_figure": alarm_figure,
    }


def _plot_qber_validation(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    for length, group in summary.groupby("sifted_length"):
        ax.scatter(
            100.0 * group["expected_qber_exact"],
            100.0 * group["mean_measured_qber"],
            label=f"K={length}",
            alpha=0.8,
        )
    limits = [
        0.0,
        100.0
        * max(
            summary["expected_qber_exact"].max(),
            summary["mean_measured_qber"].max(),
        )
        * 1.05,
    ]
    ax.plot(limits, limits, color="black", linestyle="--", label="ideal agreement")
    ax.set_xlim(limits)
    ax.set_ylim(limits)
    ax.set_xlabel("Exact expected QBER (%)")
    ax.set_ylabel("Bit-level mean measured QBER (%)")
    ax.set_title("Bit-level validation of expected QBER")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_alarm_validation(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    for length, group in summary.groupby("sifted_length"):
        ax.scatter(
            group["theoretical_alarm_rate"],
            group["empirical_alarm_rate"],
            label=f"K={length}",
            alpha=0.8,
        )
    ax.plot([0.0, 1.0], [0.0, 1.0], color="black", linestyle="--")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("Exact-binomial alarm probability")
    ax.set_ylabel("Bit-level empirical alarm rate")
    ax.set_title("Bit-level validation of detector probabilities")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _trial_seed(
    master_seed: int,
    actual_baseline: float,
    eve_interception: float,
    sifted_length: int,
    condition_trial: int,
) -> int:
    payload = (
        f"{master_seed}|{actual_baseline:.12g}|{eve_interception:.12g}|"
        f"{sifted_length}|{condition_trial}"
    ).encode("utf-8")
    return int.from_bytes(
        hashlib.blake2b(payload, digest_size=8).digest(), "little"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=2028)
    parser.add_argument(
        "--output-directory",
        default="research/results/full_bb84_validation",
    )
    parser.add_argument(
        "--figure-directory",
        default="research/figures/full_bb84_validation",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = FullBB84ValidationConfig(
        trials_per_condition=args.trials,
        master_seed=args.seed,
    )
    trials, summary = run_full_bb84_validation(config)
    paths = save_validation(
        trials,
        summary,
        config,
        output_directory=args.output_directory,
        figure_directory=args.figure_directory,
    )
    print(
        f"Completed {len(summary)} conditions and {len(trials):,} bit-level trials."
    )
    print(
        "Maximum absolute mean-QBER discrepancy: "
        f"{summary['qber_mean_minus_theory'].abs().max():.6f}"
    )
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
