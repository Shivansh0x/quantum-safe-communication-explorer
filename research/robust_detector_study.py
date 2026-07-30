"""Compare fixed-baseline and uncertainty-aware BB84 QBER detectors.

The uncertainty-aware detector assumes that the no-Eve baseline QBER is no
greater than b_a + u, where u is a declared uncertainty margin. It calibrates
its exact-binomial threshold at that upper bound. Because binomial upper tails
increase with the error probability, this controls the theoretical false-alarm
rate for every actual baseline at or below the declared upper bound.

Run from the repository root:

    python -m research.robust_detector_study
"""

from __future__ import annotations

import argparse
import hashlib
import json
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


SCRIPT_VERSION = "1.0.0"


@dataclass(frozen=True)
class RobustDetectorConfig:
    assumed_baseline: float = 0.03
    uncertainty_margins: tuple[float, ...] = (0.00, 0.005, 0.01, 0.02)
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
    master_seed: int = 2027

    def validate(self) -> None:
        _validate_probability("assumed_baseline", self.assumed_baseline)
        _validate_probability("alpha", self.alpha, positive=True)
        for margin in self.uncertainty_margins:
            if margin < 0.0:
                raise ValueError("uncertainty margins cannot be negative.")
            if self.assumed_baseline + margin > 1.0:
                raise ValueError("assumed baseline plus margin cannot exceed 1.")
        for baseline in self.actual_baselines:
            _validate_probability("actual_baseline", baseline)
        for interception in self.eve_interceptions:
            _validate_probability("eve_interception", interception)
        if any(length <= 0 for length in self.sifted_lengths):
            raise ValueError("sifted lengths must be positive.")
        if self.trials_per_condition <= 0:
            raise ValueError("trials_per_condition must be positive.")


def run_robust_detector_study(config: RobustDetectorConfig) -> pd.DataFrame:
    config.validate()
    rows: list[dict] = []

    for margin in config.uncertainty_margins:
        calibration_baseline = config.assumed_baseline + margin
        for sifted_length in config.sifted_lengths:
            critical_count = critical_error_count(
                sifted_length=sifted_length,
                assumed_baseline=calibration_baseline,
                alpha=config.alpha,
            )
            worst_case_fpr = theoretical_detection_probability(
                error_probability=calibration_baseline,
                sifted_length=sifted_length,
                critical_count=critical_count,
            )

            for actual_baseline in config.actual_baselines:
                mismatch = actual_baseline - config.assumed_baseline
                baseline_within_declared_bound = (
                    actual_baseline <= calibration_baseline + 1e-15
                )
                for eve_interception in config.eve_interceptions:
                    actual_qber = expected_qber_exact(
                        actual_baseline, eve_interception
                    )
                    theoretical_rate = theoretical_detection_probability(
                        error_probability=actual_qber,
                        sifted_length=sifted_length,
                        critical_count=critical_count,
                    )
                    condition_seed = _condition_seed(
                        config.master_seed,
                        margin,
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
                    alarm_count = int(np.count_nonzero(error_counts >= critical_count))
                    empirical_rate = alarm_count / config.trials_per_condition
                    ci_low, ci_high = wilson_interval(
                        alarm_count, config.trials_per_condition
                    )

                    rows.append(
                        {
                            "script_version": SCRIPT_VERSION,
                            "master_seed": config.master_seed,
                            "condition_seed": condition_seed,
                            "trials": config.trials_per_condition,
                            "alpha": config.alpha,
                            "sifted_length": sifted_length,
                            "assumed_baseline": config.assumed_baseline,
                            "uncertainty_margin": margin,
                            "calibration_baseline_upper": calibration_baseline,
                            "actual_baseline": actual_baseline,
                            "baseline_mismatch": mismatch,
                            "baseline_within_declared_bound": (
                                baseline_within_declared_bound
                            ),
                            "eve_interception": eve_interception,
                            "actual_qber": actual_qber,
                            "critical_error_count": critical_count,
                            "critical_qber": critical_count / sifted_length,
                            "worst_case_fpr_within_bound": worst_case_fpr,
                            "alarm_count": alarm_count,
                            "empirical_alarm_rate": empirical_rate,
                            "alarm_rate_ci_low": ci_low,
                            "alarm_rate_ci_high": ci_high,
                            "theoretical_alarm_rate": theoretical_rate,
                            "monte_carlo_minus_theory": (
                                empirical_rate - theoretical_rate
                            ),
                            "false_positive_rate": (
                                empirical_rate
                                if eve_interception == 0.0
                                else np.nan
                            ),
                            "detection_power": (
                                empirical_rate
                                if eve_interception > 0.0
                                else np.nan
                            ),
                            "false_negative_rate": (
                                1.0 - empirical_rate
                                if eve_interception > 0.0
                                else np.nan
                            ),
                        }
                    )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "uncertainty_margin",
                "sifted_length",
                "actual_baseline",
                "eve_interception",
            ]
        )
        .reset_index(drop=True)
    )


def save_robust_study(
    summary: pd.DataFrame,
    config: RobustDetectorConfig,
    *,
    output_directory: str | Path = "research/results/robust_detector_study",
    figure_directory: str | Path = "research/figures/robust_detector_study",
) -> dict[str, Path]:
    output_path = Path(output_directory)
    figure_path = Path(figure_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    figure_path.mkdir(parents=True, exist_ok=True)

    summary_path = output_path / "robust_detector_summary.csv"
    guarantee_path = output_path / "robust_detector_guarantee_check.csv"
    config_path = output_path / "robust_detector_config.json"

    summary.to_csv(summary_path, index=False)
    guarantee = summary[
        np.isclose(summary["eve_interception"], 0.0)
        & summary["baseline_within_declared_bound"]
    ].copy()
    guarantee["theoretical_fpr_controlled"] = (
        guarantee["theoretical_alarm_rate"] <= guarantee["alpha"] + 1e-15
    )
    guarantee.to_csv(guarantee_path, index=False)

    metadata = {
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": asdict(config),
        "method": (
            "Threshold is calibrated at assumed_baseline + uncertainty_margin. "
            "For no-Eve baselines not exceeding that upper bound, monotonicity "
            "of the binomial upper tail gives theoretical FPR <= alpha."
        ),
    }
    config_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    fpr_path = figure_path / "robust_fpr_comparison_k1000.png"
    power_path = figure_path / "robust_power_tradeoff_k1000.png"
    _plot_fpr_comparison(summary, fpr_path, sifted_length=1000)
    _plot_power_tradeoff(summary, power_path, sifted_length=1000)

    return {
        "summary": summary_path,
        "guarantee_check": guarantee_path,
        "config": config_path,
        "fpr_figure": fpr_path,
        "power_figure": power_path,
    }


def _plot_fpr_comparison(
    summary: pd.DataFrame, path: Path, *, sifted_length: int
) -> None:
    data = summary[
        (summary["sifted_length"] == sifted_length)
        & np.isclose(summary["eve_interception"], 0.0)
    ]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for margin, group in data.groupby("uncertainty_margin"):
        group = group.sort_values("baseline_mismatch")
        ax.plot(
            100.0 * group["baseline_mismatch"],
            group["theoretical_alarm_rate"],
            marker="o",
            markersize=3,
            label=f"margin={100*margin:.1f} pp",
        )
    ax.axhline(0.01, color="gray", linestyle="--", label="alpha=1%")
    ax.axvline(0.0, color="black", linestyle=":")
    ax.set_xlabel("Actual minus assumed baseline QBER (percentage points)")
    ax.set_ylabel("Theoretical false-positive rate")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"Uncertainty-aware false-alarm control at K={sifted_length}")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_power_tradeoff(
    summary: pd.DataFrame, path: Path, *, sifted_length: int
) -> None:
    data = summary[
        (summary["sifted_length"] == sifted_length)
        & np.isclose(summary["baseline_mismatch"], 0.0)
    ]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for margin, group in data.groupby("uncertainty_margin"):
        group = group.sort_values("eve_interception")
        ax.plot(
            100.0 * group["eve_interception"],
            group["theoretical_alarm_rate"],
            marker="o",
            markersize=3,
            label=f"margin={100*margin:.1f} pp",
        )
    ax.set_xlabel("Eve interception density (%)")
    ax.set_ylabel("Alarm probability")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"False-alarm versus detection-power tradeoff at K={sifted_length}")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _condition_seed(
    master_seed: int,
    margin: float,
    actual_baseline: float,
    eve_interception: float,
    sifted_length: int,
) -> int:
    payload = (
        f"{master_seed}|{margin:.12g}|{actual_baseline:.12g}|"
        f"{eve_interception:.12g}|{sifted_length}"
    ).encode("utf-8")
    return int.from_bytes(
        hashlib.blake2b(payload, digest_size=8).digest(), "little"
    )


def _validate_probability(name: str, value: float, *, positive: bool = False) -> None:
    lower_ok = value > 0.0 if positive else value >= 0.0
    if not lower_ok or value > 1.0:
        raise ValueError(f"{name} is outside its valid probability range.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument(
        "--output-directory",
        default="research/results/robust_detector_study",
    )
    parser.add_argument(
        "--figure-directory",
        default="research/figures/robust_detector_study",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = RobustDetectorConfig(
        trials_per_condition=args.trials,
        master_seed=args.seed,
    )
    summary = run_robust_detector_study(config)
    paths = save_robust_study(
        summary,
        config,
        output_directory=args.output_directory,
        figure_directory=args.figure_directory,
    )
    guarantee = summary[
        np.isclose(summary["eve_interception"], 0.0)
        & summary["baseline_within_declared_bound"]
    ]
    violations = int(
        np.count_nonzero(guarantee["theoretical_alarm_rate"] > config.alpha + 1e-15)
    )
    print(
        f"Completed {len(summary)} conditions with "
        f"{config.trials_per_condition:,} trials per condition."
    )
    print(f"Theoretical within-bound FPR violations: {violations}")
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

