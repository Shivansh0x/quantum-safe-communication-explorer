"""Combined BB84 detector robustness study.

This module studies a QBER-threshold detector under:

* correct and incorrect baseline-QBER assumptions,
* partial intercept-resend attacks,
* several finite sifted-key lengths, and
* additive versus exact-model interception estimators.

Run from the repository root:

    python -m research.detector_study

The simulation uses direct binomial sampling because, under the validated iid
model, the error count among K tested sifted bits is Binomial(K, q). Selected
conditions will later be cross-validated with the slower bit-level simulator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import binom

from research.model_validation import expected_qber_exact


SCRIPT_VERSION = "1.0.1"


@dataclass(frozen=True)
class DetectorStudyConfig:
    assumed_baseline: float = 0.03
    actual_baselines: tuple[float, ...] = (
        0.01,
        0.015,
        0.02,
        0.025,
        0.03,
        0.035,
        0.04,
        0.045,
        0.05,
    )
    eve_interceptions: tuple[float, ...] = (0.00, 0.02, 0.05, 0.10, 0.20)
    sifted_lengths: tuple[int, ...] = (250, 500, 1000, 2500, 5000)
    alpha: float = 0.01
    trials_per_condition: int = 20_000
    master_seed: int = 2026

    def validate(self) -> None:
        _validate_probability("assumed_baseline", self.assumed_baseline)
        _validate_probability("alpha", self.alpha, inclusive_zero=False)
        for value in self.actual_baselines:
            _validate_probability("actual_baseline", value)
        for value in self.eve_interceptions:
            _validate_probability("eve_interception", value)
        if not self.sifted_lengths or any(k <= 0 for k in self.sifted_lengths):
            raise ValueError("Every sifted length must be positive.")
        if self.trials_per_condition <= 0:
            raise ValueError("trials_per_condition must be positive.")


def critical_error_count(
    *, sifted_length: int, assumed_baseline: float, alpha: float
) -> int:
    """Return the smallest c with P(X >= c | b_a) <= alpha.

    Returning K + 1 is allowed and represents a detector that can never alarm.
    Binary search avoids off-by-one ambiguity in inverse-survival functions.
    """
    if sifted_length <= 0:
        raise ValueError("sifted_length must be positive.")
    _validate_probability("assumed_baseline", assumed_baseline)
    _validate_probability("alpha", alpha, inclusive_zero=False)

    low, high = 0, sifted_length + 1
    while low < high:
        candidate = (low + high) // 2
        tail = float(binom.sf(candidate - 1, sifted_length, assumed_baseline))
        if tail <= alpha:
            high = candidate
        else:
            low = candidate + 1
    return low


def theoretical_detection_probability(
    *, error_probability: float, sifted_length: int, critical_count: int
) -> float:
    """Calculate P(X >= critical_count) for a binomial error count."""
    _validate_probability("error_probability", error_probability)
    if sifted_length <= 0:
        raise ValueError("sifted_length must be positive.")
    if not 0 <= critical_count <= sifted_length + 1:
        raise ValueError("critical_count must lie between 0 and K + 1.")
    return float(binom.sf(critical_count - 1, sifted_length, error_probability))


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise ValueError("trials must be positive.")
    if not 0 <= successes <= trials:
        raise ValueError("successes must lie between 0 and trials.")
    estimate = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (estimate + z2 / (2.0 * trials)) / denominator
    half_width = (
        z
        * np.sqrt(
            estimate * (1.0 - estimate) / trials
            + z2 / (4.0 * trials * trials)
        )
        / denominator
    )
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)

    # At the two boundaries the Wilson endpoints are exactly 0 and 1.
    # Set them explicitly to avoid tiny floating-point residuals.
    if successes == 0:
        lower = 0.0
    if successes == trials:
        upper = 1.0

    return lower, upper


def run_detector_study(config: DetectorStudyConfig) -> pd.DataFrame:
    """Run the full detector and estimator grid, returning one row per condition."""
    config.validate()
    rows: list[dict] = []

    for sifted_length in config.sifted_lengths:
        critical_count = critical_error_count(
            sifted_length=sifted_length,
            assumed_baseline=config.assumed_baseline,
            alpha=config.alpha,
        )
        calibrated_fpr = theoretical_detection_probability(
            error_probability=config.assumed_baseline,
            sifted_length=sifted_length,
            critical_count=critical_count,
        )

        for actual_baseline in config.actual_baselines:
            delta = actual_baseline - config.assumed_baseline
            for eve_interception in config.eve_interceptions:
                actual_qber = expected_qber_exact(
                    actual_baseline, eve_interception
                )
                condition_seed = _condition_seed(
                    config.master_seed,
                    config.assumed_baseline,
                    actual_baseline,
                    eve_interception,
                    sifted_length,
                )
                rng = np.random.default_rng(condition_seed)
                error_counts = rng.binomial(
                    sifted_length,
                    actual_qber,
                    size=config.trials_per_condition,
                )
                measured_qber = error_counts / sifted_length
                alarms = error_counts >= critical_count
                alarm_count = int(np.count_nonzero(alarms))
                empirical_detection_rate = alarm_count / config.trials_per_condition
                interval_low, interval_high = wilson_interval(
                    alarm_count, config.trials_per_condition
                )
                theoretical_rate = theoretical_detection_probability(
                    error_probability=actual_qber,
                    sifted_length=sifted_length,
                    critical_count=critical_count,
                )

                additive_raw = 4.0 * (
                    measured_qber - config.assumed_baseline
                )
                exact_assumed_denominator = (
                    0.25 - config.assumed_baseline / 2.0
                )
                exact_assumed_raw = (
                    measured_qber - config.assumed_baseline
                ) / exact_assumed_denominator
                exact_oracle_denominator = 0.25 - actual_baseline / 2.0
                exact_oracle_raw = (
                    measured_qber - actual_baseline
                ) / exact_oracle_denominator

                estimator_metrics = {}
                estimator_metrics.update(
                    _estimator_metrics(
                        "additive_raw", additive_raw, eve_interception
                    )
                )
                estimator_metrics.update(
                    _estimator_metrics(
                        "additive_clipped",
                        np.clip(additive_raw, 0.0, 1.0),
                        eve_interception,
                    )
                )
                estimator_metrics.update(
                    _estimator_metrics(
                        "exact_assumed_raw",
                        exact_assumed_raw,
                        eve_interception,
                    )
                )
                estimator_metrics.update(
                    _estimator_metrics(
                        "exact_assumed_clipped",
                        np.clip(exact_assumed_raw, 0.0, 1.0),
                        eve_interception,
                    )
                )
                estimator_metrics.update(
                    _estimator_metrics(
                        "exact_oracle_raw", exact_oracle_raw, eve_interception
                    )
                )

                row = {
                    "script_version": SCRIPT_VERSION,
                    "master_seed": config.master_seed,
                    "condition_seed": condition_seed,
                    "trials": config.trials_per_condition,
                    "alpha": config.alpha,
                    "sifted_length": sifted_length,
                    "assumed_baseline": config.assumed_baseline,
                    "actual_baseline": actual_baseline,
                    "baseline_mismatch": delta,
                    "eve_interception": eve_interception,
                    "actual_qber": actual_qber,
                    "critical_error_count": critical_count,
                    "critical_qber": critical_count / sifted_length,
                    "calibrated_fpr_theoretical": calibrated_fpr,
                    "mean_measured_qber": float(np.mean(measured_qber)),
                    "sd_measured_qber": float(
                        np.std(measured_qber, ddof=1)
                    ),
                    "alarm_count": alarm_count,
                    "empirical_detection_rate": empirical_detection_rate,
                    "detection_rate_ci_low": interval_low,
                    "detection_rate_ci_high": interval_high,
                    "theoretical_detection_rate": theoretical_rate,
                    "monte_carlo_minus_theory": (
                        empirical_detection_rate - theoretical_rate
                    ),
                    "false_positive_rate": (
                        empirical_detection_rate
                        if eve_interception == 0.0
                        else np.nan
                    ),
                    "true_positive_rate": (
                        empirical_detection_rate
                        if eve_interception > 0.0
                        else np.nan
                    ),
                    "false_negative_rate": (
                        1.0 - empirical_detection_rate
                        if eve_interception > 0.0
                        else np.nan
                    ),
                }
                row.update(estimator_metrics)
                rows.append(row)

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["sifted_length", "actual_baseline", "eve_interception"]
        )
        .reset_index(drop=True)
    )


def save_study(
    summary: pd.DataFrame,
    config: DetectorStudyConfig,
    *,
    output_directory: str | Path = "research/results/detector_study",
    figure_directory: str | Path = "research/figures/detector_study",
) -> dict[str, Path]:
    """Save summaries, configuration metadata, and initial figures."""
    output_path = Path(output_directory)
    figure_path = Path(figure_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    figure_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "detector_study_summary.csv"
    calibration_path = output_path / "detector_calibration_summary.csv"
    config_path = output_path / "detector_study_config.json"

    summary.to_csv(summary_path, index=False)
    calibration = summary[
        np.isclose(summary["baseline_mismatch"], 0.0)
        & np.isclose(summary["eve_interception"], 0.0)
    ].copy()
    calibration.to_csv(calibration_path, index=False)

    metadata = {
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": asdict(config),
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "matplotlib": plt.matplotlib.__version__,
        },
        "data_policy": (
            "Condition-level results are saved. Individual pseudo-random "
            "draws are reproducible from condition_seed and configuration."
        ),
    }
    config_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    fpr_figure = figure_path / "false_positive_rate_vs_mismatch.png"
    power_figure = figure_path / "detection_power_vs_interception.png"
    bias_figure = figure_path / "exact_estimator_bias_vs_mismatch.png"
    _plot_false_positive_rate(summary, fpr_figure)
    _plot_detection_power(summary, power_figure)
    _plot_estimator_bias(summary, bias_figure)

    return {
        "summary": summary_path,
        "calibration": calibration_path,
        "config": config_path,
        "fpr_figure": fpr_figure,
        "power_figure": power_figure,
        "bias_figure": bias_figure,
    }


def _estimator_metrics(prefix: str, estimates: np.ndarray, truth: float) -> dict:
    differences = estimates - truth
    return {
        f"{prefix}_mean": float(np.mean(estimates)),
        f"{prefix}_bias": float(np.mean(differences)),
        f"{prefix}_mae": float(np.mean(np.abs(differences))),
        f"{prefix}_rmse": float(np.sqrt(np.mean(differences * differences))),
        f"{prefix}_fraction_below_zero": float(np.mean(estimates < 0.0)),
        f"{prefix}_fraction_above_one": float(np.mean(estimates > 1.0)),
    }


def _condition_seed(
    master_seed: int,
    assumed_baseline: float,
    actual_baseline: float,
    eve_interception: float,
    sifted_length: int,
) -> int:
    payload = (
        f"{master_seed}|{assumed_baseline:.12g}|{actual_baseline:.12g}|"
        f"{eve_interception:.12g}|{sifted_length}"
    ).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, "little", signed=False)


def _plot_false_positive_rate(summary: pd.DataFrame, path: Path) -> None:
    data = summary[np.isclose(summary["eve_interception"], 0.0)]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for sifted_length, group in data.groupby("sifted_length"):
        group = group.sort_values("baseline_mismatch")
        x = 100.0 * group["baseline_mismatch"]
        ax.plot(
            x,
            group["theoretical_detection_rate"],
            label=f"K={sifted_length}",
        )
        ax.scatter(x, group["empirical_detection_rate"], s=18)
    ax.axvline(0.0, color="black", linewidth=1, linestyle=":")
    ax.axhline(0.01, color="gray", linewidth=1, linestyle="--", label="alpha=1%")
    ax.set_xlabel("Baseline mismatch, actual minus assumed (percentage points)")
    ax.set_ylabel("False-positive rate")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("False alarms under baseline-QBER mismatch")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_detection_power(summary: pd.DataFrame, path: Path) -> None:
    lengths = sorted(summary["sifted_length"].unique())
    selected_lengths = [lengths[0], lengths[len(lengths) // 2], lengths[-1]]
    mismatches = sorted(summary["baseline_mismatch"].unique())
    selected_mismatches = [mismatches[0], min(mismatches, key=abs), mismatches[-1]]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5), sharey=True)
    for ax, sifted_length in zip(axes, selected_lengths):
        for mismatch in selected_mismatches:
            group = summary[
                (summary["sifted_length"] == sifted_length)
                & np.isclose(summary["baseline_mismatch"], mismatch)
            ].sort_values("eve_interception")
            ax.plot(
                100.0 * group["eve_interception"],
                group["theoretical_detection_rate"],
                label=f"delta={100*mismatch:+.1f} pp",
            )
            ax.scatter(
                100.0 * group["eve_interception"],
                group["empirical_detection_rate"],
                s=18,
            )
        ax.set_title(f"K={sifted_length}")
        ax.set_xlabel("Eve interception density (%)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Detection probability")
    axes[-1].legend()
    fig.suptitle("Alarm probability under baseline-QBER mismatch")
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_estimator_bias(summary: pd.DataFrame, path: Path) -> None:
    lengths = sorted(summary["sifted_length"].unique())
    selected_length = lengths[len(lengths) // 2]
    data = summary[summary["sifted_length"] == selected_length]

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for interception, group in data.groupby("eve_interception"):
        group = group.sort_values("baseline_mismatch")
        ax.plot(
            100.0 * group["baseline_mismatch"],
            100.0 * group["exact_assumed_raw_bias"],
            marker="o",
            markersize=3,
            label=f"p={100*interception:.0f}%",
        )
    ax.axhline(0.0, color="black", linewidth=1, linestyle=":")
    ax.axvline(0.0, color="black", linewidth=1, linestyle=":")
    ax.set_xlabel("Baseline mismatch (percentage points)")
    ax.set_ylabel("Interception-estimate bias (percentage points)")
    ax.set_title(
        f"Bias of exact-model estimator using assumed baseline at K={selected_length}"
    )
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _validate_probability(
    name: str, value: float, *, inclusive_zero: bool = True
) -> None:
    lower_ok = value >= 0.0 if inclusive_zero else value > 0.0
    if not lower_ok or value > 1.0:
        boundary = "[0, 1]" if inclusive_zero else "(0, 1]"
        raise ValueError(f"{name} must lie in {boundary}.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--assumed-baseline", type=float, default=0.03)
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument(
        "--output-directory", default="research/results/detector_study"
    )
    parser.add_argument(
        "--figure-directory", default="research/figures/detector_study"
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = DetectorStudyConfig(
        assumed_baseline=args.assumed_baseline,
        alpha=args.alpha,
        trials_per_condition=args.trials,
        master_seed=args.seed,
    )
    summary = run_detector_study(config)
    paths = save_study(
        summary,
        config,
        output_directory=args.output_directory,
        figure_directory=args.figure_directory,
    )
    print(
        f"Completed {len(summary)} conditions with "
        f"{config.trials_per_condition:,} trials per condition."
    )
    for name, path in paths.items():
        print(f"{name}: {path}")
    calibration_columns = [
        "sifted_length",
        "critical_error_count",
        "critical_qber",
        "calibrated_fpr_theoretical",
        "empirical_detection_rate",
        "detection_rate_ci_low",
        "detection_rate_ci_high",
    ]
    calibration = summary[
        np.isclose(summary["baseline_mismatch"], 0.0)
        & np.isclose(summary["eve_interception"], 0.0)
    ]
    print("\nCorrect-calibration check:")
    print(calibration[calibration_columns].to_string(index=False))


if __name__ == "__main__":
    main()
