"""Data-driven uncertainty margin for the BB84 baseline-QBER detector.

Adds a fifth experiment to the baseline-QBER mismatch study.

Instead of fixing the upward uncertainty margin u by hand, this experiment
derives it from a no-attack calibration period of N_cal sifted bits:

    b_U = ClopperPearsonUpper(X_cal, N_cal, beta)
    c_u = min{ m : Pr_{b_U}(X >= m) <= alpha }

Because the Clopper-Pearson upper bound covers b_t with probability at least
1 - beta, and because the binomial upper tail is nondecreasing in its success
probability, the unconditional no-attack alarm probability of the resulting
detector is at most alpha + beta.

The experiment measures the realised margin, the false-alarm probability, and
the detection power as a function of the calibration budget N_cal.

Run from the repository root:

    python -m research.calibration_budget_study
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import beta as beta_dist
from scipy.stats import binom

SCRIPT_VERSION = "1.0.0"
MASTER_SEED = 2029

ASSUMED_ALPHA = 0.01
SIFTED_LENGTH = 1000
ACTUAL_BASELINE = 0.03
INTERCEPTION_DENSITIES = (0.0, 0.05, 0.10, 0.20)
CALIBRATION_BUDGETS = (1_000, 2_500, 5_000, 10_000, 25_000, 100_000)
CALIBRATION_LEVELS = (0.01, 0.001)
TRIALS = 40_000


@dataclass(frozen=True)
class Condition:
    calibration_bits: int
    calibration_level: float
    interception_density: float


def expected_qber(actual_baseline: float, interception_density: float) -> float:
    """Expected sifted-bit error probability under partial intercept-resend."""
    if not 0.0 <= actual_baseline <= 1.0:
        raise ValueError("actual_baseline must lie in [0, 1]")
    if not 0.0 <= interception_density <= 1.0:
        raise ValueError("interception_density must lie in [0, 1]")
    return actual_baseline + interception_density * (0.25 - actual_baseline / 2.0)


def clopper_pearson_upper(errors: int, trials: int, level: float) -> float:
    """One-sided Clopper-Pearson upper confidence bound at level 1 - `level`."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= errors <= trials:
        raise ValueError("errors must lie in [0, trials]")
    if errors == trials:
        return 1.0
    return float(beta_dist.ppf(1.0 - level, errors + 1, trials - errors))


def critical_count(sifted_length: int, baseline: float, alpha: float) -> int:
    """Smallest m in {0, ..., K + 1} with Pr_baseline(X >= m) <= alpha."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    baseline = min(max(baseline, 0.0), 1.0)
    if baseline >= 1.0:
        return sifted_length + 1
    start = int(binom.isf(alpha, sifted_length, baseline))
    candidate = max(0, start - 5)
    while candidate <= sifted_length:
        if binom.sf(candidate - 1, sifted_length, baseline) <= alpha:
            return candidate
        candidate += 1
    return sifted_length + 1


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054):
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    phat = successes / trials
    denom = 1.0 + z * z / trials
    centre = (phat + z * z / (2.0 * trials)) / denom
    halfwidth = (
        z * np.sqrt(phat * (1.0 - phat) / trials + z * z / (4.0 * trials * trials))
    ) / denom
    return max(0.0, centre - halfwidth), min(1.0, centre + halfwidth)


def condition_seed(master_seed: int, condition: Condition) -> int:
    """Deterministic per-condition seed, matching the convention used by the
    other research modules."""
    payload = (
        f"{master_seed}|{condition.calibration_bits}|"
        f"{condition.calibration_level:.12g}|"
        f"{condition.interception_density:.12g}"
    ).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, "little", signed=False)


def run_condition(condition: Condition, trials: int = TRIALS) -> dict:
    rng = np.random.default_rng(condition_seed(MASTER_SEED, condition))

    calibration_errors = rng.binomial(
        condition.calibration_bits, ACTUAL_BASELINE, trials
    )
    upper_bounds = np.array(
        [
            clopper_pearson_upper(
                int(errors), condition.calibration_bits, condition.calibration_level
            )
            for errors in calibration_errors
        ]
    )

    # Cache thresholds: many calibration draws map to the same upper bound.
    unique_bounds, inverse = np.unique(upper_bounds, return_inverse=True)
    unique_thresholds = np.array(
        [critical_count(SIFTED_LENGTH, b, ASSUMED_ALPHA) for b in unique_bounds]
    )
    thresholds = unique_thresholds[inverse]

    qber = expected_qber(ACTUAL_BASELINE, condition.interception_density)
    observed_errors = rng.binomial(SIFTED_LENGTH, qber, trials)
    alarms = int(np.sum(observed_errors >= thresholds))
    alarm_rate = alarms / trials
    ci_low, ci_high = wilson_interval(alarms, trials)

    return {
        "script_version": SCRIPT_VERSION,
        "master_seed": MASTER_SEED,
        "condition_seed": condition_seed(MASTER_SEED, condition),
        "trials": trials,
        "alpha": ASSUMED_ALPHA,
        "calibration_level": condition.calibration_level,
        "calibration_bits": condition.calibration_bits,
        "sifted_length": SIFTED_LENGTH,
        "actual_baseline": ACTUAL_BASELINE,
        "interception_density": condition.interception_density,
        "actual_qber": qber,
        "mean_margin": float(np.mean(upper_bounds - ACTUAL_BASELINE)),
        "sd_margin": float(np.std(upper_bounds - ACTUAL_BASELINE, ddof=1)),
        "coverage_fraction": float(np.mean(upper_bounds >= ACTUAL_BASELINE)),
        "mean_critical_count": float(np.mean(thresholds)),
        "alarm_count": alarms,
        "empirical_alarm_rate": alarm_rate,
        "alarm_rate_ci_low": ci_low,
        "alarm_rate_ci_high": ci_high,
        "unconditional_bound": ASSUMED_ALPHA + condition.calibration_level,
        "bound_respected": bool(
            condition.interception_density > 0.0
            or alarm_rate <= ASSUMED_ALPHA + condition.calibration_level
        ),
    }


def _plot_power_versus_budget(
    summary: pd.DataFrame, path: Path, *, calibration_level: float
) -> None:
    data = summary[np.isclose(summary["calibration_level"], calibration_level)]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for density, group in data.groupby("interception_density"):
        if np.isclose(density, 0.0):
            continue
        group = group.sort_values("calibration_bits")
        ax.plot(
            group["calibration_bits"],
            group["empirical_alarm_rate"],
            marker="o",
            markersize=3,
            label=f"p={100 * density:.0f}%",
        )
        threshold = critical_count(SIFTED_LENGTH, ACTUAL_BASELINE, ASSUMED_ALPHA)
        oracle = binom.sf(
            threshold - 1, SIFTED_LENGTH, expected_qber(ACTUAL_BASELINE, density)
        )
        ax.axhline(oracle, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("Calibration budget (sifted bits)")
    ax.set_ylabel("Detection power")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(
        f"Detection power versus calibration budget at K={SIFTED_LENGTH}, "
        f"beta={calibration_level:g} (dashed: oracle)"
    )
    ax.grid(alpha=0.25)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_margin_versus_budget(summary: pd.DataFrame, path: Path) -> None:
    data = summary[np.isclose(summary["interception_density"], 0.0)]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for level, group in data.groupby("calibration_level"):
        group = group.sort_values("calibration_bits")
        ax.plot(
            group["calibration_bits"],
            100.0 * group["mean_margin"],
            marker="o",
            markersize=3,
            label=f"beta={level:g}",
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Calibration budget (sifted bits)")
    ax.set_ylabel("Mean realised margin (percentage points)")
    ax.set_title("Clopper-Pearson margin versus calibration budget")
    ax.grid(alpha=0.25, which="both")
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def oracle_reference() -> dict:
    """Fixed detector calibrated at the true baseline: an upper bound on power."""
    threshold = critical_count(SIFTED_LENGTH, ACTUAL_BASELINE, ASSUMED_ALPHA)
    row = {"critical_count": threshold}
    for density in INTERCEPTION_DENSITIES:
        qber = expected_qber(ACTUAL_BASELINE, density)
        row[f"alarm_p{int(density * 100)}"] = float(
            binom.sf(threshold - 1, SIFTED_LENGTH, qber)
        )
    return row


def main() -> None:
    conditions = [
        Condition(bits, level, density)
        for bits in CALIBRATION_BUDGETS
        for level in CALIBRATION_LEVELS
        for density in INTERCEPTION_DENSITIES
    ]
    rows = [run_condition(condition) for condition in conditions]
    frame = pd.DataFrame(rows)

    results_dir = Path("research/results/calibration_budget_study")
    figures_dir = Path("research/figures/calibration_budget_study")
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    frame.to_csv(results_dir / "calibration_budget_summary.csv", index=False)

    for level in CALIBRATION_LEVELS:
        _plot_power_versus_budget(
            frame,
            figures_dir / f"calibration_budget_power_beta{level:g}.png",
            calibration_level=level,
        )
    _plot_margin_versus_budget(
        frame, figures_dir / "calibration_budget_margin.png"
    )

    config = {
        "script_version": SCRIPT_VERSION,
        "master_seed": MASTER_SEED,
        "alpha": ASSUMED_ALPHA,
        "sifted_length": SIFTED_LENGTH,
        "actual_baseline": ACTUAL_BASELINE,
        "calibration_budgets": list(CALIBRATION_BUDGETS),
        "calibration_levels": list(CALIBRATION_LEVELS),
        "interception_densities": list(INTERCEPTION_DENSITIES),
        "trials": TRIALS,
        "conditions": len(conditions),
        "oracle_reference": oracle_reference(),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
    }
    (results_dir / "calibration_budget_config.json").write_text(
        json.dumps(config, indent=2)
    )

    print(frame.to_string(index=False))
    print()
    print("oracle reference:", oracle_reference())


if __name__ == "__main__":
    main()
