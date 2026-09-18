"""Finite-horizon QBER change monitoring under an unknown baseline.

This experiment deliberately separates *change detection* from attribution.
It compares three rules over a finite run of operating blocks:

1. a known-baseline oracle threshold;
2. a Clopper--Pearson upper-baseline threshold; and
3. an exact conditional two-sample test comparing calibration and operation.

The central negative result is an identifiability statement.  Within the
i.i.d. Bernoulli error model, a benign channel change and an intercept-resend
benchmark that induce the same QBER path generate the same distribution of
all observed error counts.  No decision rule using only those counts can
distinguish their causes.

The reported probabilities are evaluated analytically.  The only numerical
approximation is truncating the calibration-count sum to a support containing
all but at most ``CALIBRATION_TAIL_MASS`` probability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from math import prod
from pathlib import Path
import platform
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import beta as beta_dist
from scipy.stats import binom, hypergeom


SCRIPT_VERSION = "1.0.0"

BASELINE_QBER = 0.03
INTERCEPTION_DENSITY = 0.10
SIFTED_LENGTH = 1_000
CALIBRATION_BITS = 5_000
OPERATING_BLOCKS = 20
FAMILYWISE_ALPHA = 0.01
CALIBRATION_TAIL_MASS = 1e-12


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label: str
    interpretation: str
    qber_path: tuple[float, ...]


def expected_qber(actual_baseline: float, interception_density: float) -> float:
    """Expected QBER for the project's partial intercept-resend benchmark."""
    if not 0.0 <= actual_baseline <= 1.0:
        raise ValueError("actual_baseline must lie in [0, 1]")
    if not 0.0 <= interception_density <= 1.0:
        raise ValueError("interception_density must lie in [0, 1]")
    return actual_baseline + interception_density * (
        0.25 - actual_baseline / 2.0
    )


def clopper_pearson_upper(errors: int, trials: int, beta: float) -> float:
    """One-sided Clopper--Pearson upper bound with failure probability beta."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= errors <= trials:
        raise ValueError("errors must lie in [0, trials]")
    if not 0.0 < beta < 1.0:
        raise ValueError("beta must lie in (0, 1)")
    if errors == trials:
        return 1.0
    return float(beta_dist.ppf(1.0 - beta, errors + 1, trials - errors))


def critical_count(trials: int, probability: float, alpha: float) -> int:
    """Smallest count c with Pr[X >= c] <= alpha for X~Bin(trials,p)."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0, 1]")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    if probability == 1.0:
        return trials + 1

    candidate = max(0, int(binom.isf(alpha, trials, probability)) - 4)
    while candidate <= trials:
        if binom.sf(candidate - 1, trials, probability) <= alpha:
            return candidate
        candidate += 1
    return trials + 1


def exact_two_sample_pvalue(
    calibration_errors: int,
    calibration_bits: int,
    operating_errors: int,
    operating_bits: int,
) -> float:
    """One-sided exact conditional p-value for an increased operating QBER.

    Under the null hypothesis that both blocks share an unknown error
    probability, conditioning on the total error count makes the operating
    count hypergeometric.
    """
    if calibration_bits <= 0 or operating_bits <= 0:
        raise ValueError("block sizes must be positive")
    if not 0 <= calibration_errors <= calibration_bits:
        raise ValueError("invalid calibration error count")
    if not 0 <= operating_errors <= operating_bits:
        raise ValueError("invalid operating error count")

    total_errors = calibration_errors + operating_errors
    return float(
        hypergeom.sf(
            operating_errors - 1,
            calibration_bits + operating_bits,
            total_errors,
            operating_bits,
        )
    )


def exact_two_sample_critical_count(
    calibration_errors: int,
    calibration_bits: int,
    operating_bits: int,
    alpha: float,
) -> int:
    """Smallest operating count rejected by the exact conditional test."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    for operating_errors in range(operating_bits + 1):
        if (
            exact_two_sample_pvalue(
                calibration_errors,
                calibration_bits,
                operating_errors,
                operating_bits,
            )
            <= alpha
        ):
            return operating_errors
    return operating_bits + 1


def probability_of_any_alert(
    critical_counts: tuple[int, ...] | list[int],
    qber_path: tuple[float, ...],
    operating_bits: int,
) -> float:
    """Probability of at least one alert over independent operating blocks."""
    if len(critical_counts) != len(qber_path):
        raise ValueError("critical_counts and qber_path must have equal length")
    block_no_alert = [
        1.0 - binom.sf(count - 1, operating_bits, qber)
        for count, qber in zip(critical_counts, qber_path)
    ]
    return float(1.0 - prod(block_no_alert))


def calibration_support(
    trials: int,
    probability: float,
    omitted_mass: float = CALIBRATION_TAIL_MASS,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return a near-exact binomial support and normalized probability weights."""
    if not 0.0 < omitted_mass < 1.0:
        raise ValueError("omitted_mass must lie in (0, 1)")
    lower = max(0, int(binom.ppf(omitted_mass / 2.0, trials, probability)))
    upper = min(
        trials,
        int(binom.ppf(1.0 - omitted_mass / 2.0, trials, probability)),
    )
    counts = np.arange(lower, upper + 1, dtype=int)
    weights = binom.pmf(counts, trials, probability)
    retained_mass = float(np.sum(weights))
    weights = weights / retained_mass
    return counts, weights, retained_mass


def build_scenarios() -> list[Scenario]:
    """Construct the stationary, drift, and observationally matched scenarios."""
    attack_qber = expected_qber(BASELINE_QBER, INTERCEPTION_DENSITY)
    stationary = (BASELINE_QBER,) * OPERATING_BLOCKS
    gradual_drift = tuple(
        float(value)
        for value in np.linspace(BASELINE_QBER, attack_qber, OPERATING_BLOCKS)
    )
    matched_change = (attack_qber,) * OPERATING_BLOCKS

    return [
        Scenario(
            "stationary",
            "Stationary channel, no change",
            "No change from the calibration distribution",
            stationary,
        ),
        Scenario(
            "gradual_benign_drift",
            "Gradual benign drift",
            "Benign QBER drift from 3.00% to the matched 5.35% endpoint",
            gradual_drift,
        ),
        Scenario(
            "matched_benign_step",
            "Matched benign step",
            "No attack; channel QBER changes from 3.00% to 5.35%",
            matched_change,
        ),
        Scenario(
            "intercept_resend",
            "10% intercept-resend benchmark",
            "3.00% baseline plus 10% partial intercept-resend; QBER is 5.35%",
            matched_change,
        ),
    ]


def _oracle_probability(scenario: Scenario) -> dict:
    per_block_alpha = FAMILYWISE_ALPHA / OPERATING_BLOCKS
    threshold = critical_count(SIFTED_LENGTH, BASELINE_QBER, per_block_alpha)
    probability = probability_of_any_alert(
        [threshold] * OPERATING_BLOCKS,
        scenario.qber_path,
        SIFTED_LENGTH,
    )
    return {
        "method": "Known-baseline oracle",
        "run_alert_probability": probability,
        "per_block_alpha": per_block_alpha,
        "calibration_beta": 0.0,
        "familywise_upper_bound": FAMILYWISE_ALPHA,
        "representative_critical_count": threshold,
    }


def _calibration_averaged_probability(
    scenario: Scenario,
    *,
    method: str,
) -> tuple[dict, float]:
    counts, weights, retained_mass = calibration_support(
        CALIBRATION_BITS, BASELINE_QBER
    )

    if method == "cp":
        calibration_beta = FAMILYWISE_ALPHA / 2.0
        per_block_alpha = (
            FAMILYWISE_ALPHA - calibration_beta
        ) / OPERATING_BLOCKS
        thresholds = [
            critical_count(
                SIFTED_LENGTH,
                clopper_pearson_upper(
                    int(errors), CALIBRATION_BITS, calibration_beta
                ),
                per_block_alpha,
            )
            for errors in counts
        ]
        label = "Clopper-Pearson margin"
        familywise_bound = (
            calibration_beta + OPERATING_BLOCKS * per_block_alpha
        )
    elif method == "two_sample":
        calibration_beta = 0.0
        per_block_alpha = FAMILYWISE_ALPHA / OPERATING_BLOCKS
        thresholds = [
            exact_two_sample_critical_count(
                int(errors),
                CALIBRATION_BITS,
                SIFTED_LENGTH,
                per_block_alpha,
            )
            for errors in counts
        ]
        label = "Exact two-sample monitor"
        familywise_bound = OPERATING_BLOCKS * per_block_alpha
    else:
        raise ValueError(f"unknown method: {method}")

    conditional_probabilities = np.array(
        [
            probability_of_any_alert(
                [threshold] * OPERATING_BLOCKS,
                scenario.qber_path,
                SIFTED_LENGTH,
            )
            for threshold in thresholds
        ]
    )
    probability = float(np.dot(weights, conditional_probabilities))
    representative_index = int(np.argmax(np.cumsum(weights) >= 0.5))
    return (
        {
            "method": label,
            "run_alert_probability": probability,
            "per_block_alpha": per_block_alpha,
            "calibration_beta": calibration_beta,
            "familywise_upper_bound": familywise_bound,
            "representative_critical_count": thresholds[representative_index],
        },
        retained_mass,
    )


def evaluate_study() -> tuple[pd.DataFrame, float]:
    """Evaluate every method and scenario and return a tidy result table."""
    rows: list[dict] = []
    retained_masses: list[float] = []
    for scenario in build_scenarios():
        method_rows = [_oracle_probability(scenario)]
        cp_row, cp_mass = _calibration_averaged_probability(
            scenario, method="cp"
        )
        two_sample_row, two_sample_mass = _calibration_averaged_probability(
            scenario, method="two_sample"
        )
        retained_masses.extend([cp_mass, two_sample_mass])
        method_rows.extend([cp_row, two_sample_row])

        for method_row in method_rows:
            rows.append(
                {
                    "script_version": SCRIPT_VERSION,
                    "scenario_id": scenario.scenario_id,
                    "scenario": scenario.label,
                    "interpretation": scenario.interpretation,
                    "qber_start": scenario.qber_path[0],
                    "qber_end": scenario.qber_path[-1],
                    "calibration_baseline": BASELINE_QBER,
                    "calibration_bits": CALIBRATION_BITS,
                    "sifted_length": SIFTED_LENGTH,
                    "operating_blocks": OPERATING_BLOCKS,
                    "familywise_alpha": FAMILYWISE_ALPHA,
                    **method_row,
                }
            )
    return pd.DataFrame(rows), min(retained_masses)


def _plot_results(frame: pd.DataFrame, path: Path) -> None:
    scenarios = [scenario.label for scenario in build_scenarios()]
    methods = [
        "Known-baseline oracle",
        "Clopper-Pearson margin",
        "Exact two-sample monitor",
    ]
    colors = ["#4C78A8", "#F58518", "#54A24B"]
    width = 0.24

    fig, (ax_stationary, ax_change) = plt.subplots(
        1,
        2,
        figsize=(10.5, 5.2),
        gridspec_kw={"width_ratios": [1.0, 2.5]},
    )

    stationary_label = scenarios[0]
    for index, (method, color) in enumerate(zip(methods, colors)):
        value = 100.0 * float(
            frame[
                (frame["method"] == method)
                & (frame["scenario"] == stationary_label)
            ]["run_alert_probability"].iloc[0]
        )
        ax_stationary.bar(index, value, width=0.72, color=color, label=method)

    ax_stationary.axhline(
        100.0 * FAMILYWISE_ALPHA,
        color="black",
        linestyle="--",
        linewidth=1.0,
    )
    ax_stationary.set_ylim(0.0, 1.1)
    ax_stationary.set_ylabel("Probability of at least one alert (%)")
    ax_stationary.set_title("No change")
    ax_stationary.set_xticks(range(len(methods)))
    ax_stationary.set_xticklabels(["Oracle", "CP", "Two-sample"], rotation=25)
    ax_stationary.grid(axis="y", alpha=0.25)

    change_scenarios = scenarios[1:]
    x = np.arange(len(change_scenarios))
    for index, (method, color) in enumerate(zip(methods, colors)):
        subset = (
            frame[frame["method"] == method]
            .set_index("scenario")
            .loc[change_scenarios]
        )
        values = 100.0 * subset["run_alert_probability"].to_numpy()
        ax_change.bar(
            x + (index - 1) * width,
            values,
            width,
            label=method,
            color=color,
        )

    ax_change.set_xticks(x)
    ax_change.set_xticklabels(
        [
            "Gradual benign\ndrift",
            "Matched benign\nstep",
            "Intercept-resend\nbenchmark",
        ]
    )
    ax_change.set_ylim(0.0, 105.0)
    ax_change.set_title("Changed operating distribution")
    ax_change.grid(axis="y", alpha=0.25)
    handles, labels = ax_change.get_legend_handles_labels()
    handles.append(
        plt.Line2D(
            [0], [0], color="black", linestyle="--", linewidth=1.0
        )
    )
    labels.append("1% run-level target")
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=2,
        fontsize=9,
    )
    fig.suptitle(
        "QBER-only monitoring detects change, not its cause",
        y=0.995,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.84), w_pad=2.0)
    fig.savefig(path, dpi=240)
    plt.close(fig)


def main() -> None:
    frame, retained_mass = evaluate_study()
    results_dir = Path("research/results/two_sample_monitoring_study")
    figures_dir = Path("research/figures/two_sample_monitoring_study")
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    frame.to_csv(results_dir / "two_sample_monitoring_summary.csv", index=False)
    _plot_results(
        frame,
        figures_dir / "finite_horizon_monitoring_comparison.png",
    )

    scenarios = build_scenarios()
    config = {
        "script_version": SCRIPT_VERSION,
        "baseline_qber": BASELINE_QBER,
        "interception_density": INTERCEPTION_DENSITY,
        "matched_operating_qber": expected_qber(
            BASELINE_QBER, INTERCEPTION_DENSITY
        ),
        "sifted_length": SIFTED_LENGTH,
        "calibration_bits": CALIBRATION_BITS,
        "operating_blocks": OPERATING_BLOCKS,
        "familywise_alpha": FAMILYWISE_ALPHA,
        "calibration_tail_mass": CALIBRATION_TAIL_MASS,
        "minimum_retained_calibration_mass": retained_mass,
        "scenarios": [
            {
                **asdict(scenario),
                "qber_path": list(scenario.qber_path),
            }
            for scenario in scenarios
        ],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
    }
    (results_dir / "two_sample_monitoring_config.json").write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )

    display = frame.pivot(
        index="scenario",
        columns="method",
        values="run_alert_probability",
    )
    print((100.0 * display).round(3).to_string())
    print()
    print(f"minimum retained calibration mass: {retained_mass:.15f}")


if __name__ == "__main__":
    main()
