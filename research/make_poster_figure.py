"""Reproduce the poster's cumulative Fisher-exact alert curves.

Run from the artifact root: python -m research.make_poster_figure

This uses the tested study's scenarios, calibration weights, and thresholds.
The product of no-alert probabilities is computed conditional on the shared
calibration count BEFORE averaging, preserving dependence between tests.
No random draws are used. The PDF is vector artwork with embedded fonts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import binom

from research import two_sample_monitoring_study as study


def compute_curves() -> tuple[pd.DataFrame, pd.DataFrame, float]:
    counts, weights, retained_mass = study.calibration_support(
        study.CALIBRATION_BITS, study.BASELINE_QBER
    )
    alpha = study.FAMILYWISE_ALPHA / study.OPERATING_BLOCKS
    thresholds = np.array(
        [
            study.exact_two_sample_critical_count(
                int(count), study.CALIBRATION_BITS, study.SIFTED_LENGTH, alpha
            )
            for count in counts
        ],
        dtype=int,
    )
    rows = []
    for scenario in study.build_scenarios():
        no_alert = binom.cdf(
            thresholds[:, None] - 1,
            study.SIFTED_LENGTH,
            np.asarray(scenario.qber_path)[None, :],
        )
        cumulative = weights @ (1.0 - np.cumprod(no_alert, axis=1))
        for block, (qber, probability) in enumerate(
            zip(scenario.qber_path, cumulative), start=1
        ):
            rows.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "operating_block": block,
                    "operating_qber": qber,
                    "cumulative_alert_probability": float(probability),
                }
            )
    calibration = pd.DataFrame(
        {
            "calibration_errors": counts,
            "normalized_probability": weights,
            "two_sample_critical_count": thresholds,
        }
    )
    return pd.DataFrame(rows), calibration, retained_mass


def verify_curves(frame: pd.DataFrame, summary_path: Path) -> None:
    """Check Figure 1 against the independently saved study's run results."""
    summary = pd.read_csv(summary_path)
    expected = summary[summary["method"] == "Exact two-sample monitor"].set_index(
        "scenario_id"
    )["run_alert_probability"]
    final = frame[frame["operating_block"] == study.OPERATING_BLOCKS].set_index(
        "scenario_id"
    )["cumulative_alert_probability"]
    np.testing.assert_allclose(final.loc[expected.index], expected, rtol=0, atol=1e-11)
    wide = frame.pivot(
        index="operating_block",
        columns="scenario_id",
        values="cumulative_alert_probability",
    )
    np.testing.assert_array_equal(
        wide["matched_benign_step"], wide["intercept_resend"]
    )
    if not ((np.diff(wide.to_numpy(), axis=0) >= -1e-14).all()):
        raise AssertionError("Cumulative probabilities must be nondecreasing")
    if not ((wide.to_numpy() >= 0).all() and (wide.to_numpy() <= 1).all()):
        raise AssertionError("A probability lies outside [0, 1]")
    if wide["stationary"].iloc[-1] > study.FAMILYWISE_ALPHA:
        raise AssertionError("Stationary run probability exceeds the declared budget")


def draw_figure(frame: pd.DataFrame, figures: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(3.32, 2.42))
    styles = [
        ("matched_benign_step", "Matched benign step", "#0072B2", "o", "-"),
        ("intercept_resend", "10% intercept-resend", "#D55E00", "x", "--"),
        ("gradual_benign_drift", "Gradual benign drift", "#009E73", "^", "-"),
        ("stationary", "Stationary (no change)", "#666666", "s", "-"),
    ]
    for scenario, label, color, marker, linestyle in styles:
        series = frame[frame["scenario_id"] == scenario]
        ax.plot(
            series["operating_block"],
            series["cumulative_alert_probability"],
            label=label,
            color=color,
            marker=marker,
            markersize=3.5,
            markerfacecolor="none" if marker == "o" else color,
            markeredgewidth=0.7,
            linewidth=0.9,
            linestyle=linestyle,
        )
    ax.axhline(study.FAMILYWISE_ALPHA, color="#333333", linestyle="--", linewidth=0.8)
    ax.text(19.8, 0.055, "1% run-level budget", ha="right", fontsize=6.5, color="#444444")
    ax.set(xlabel="Operating block", ylabel="Cumulative alert probability")
    ax.set_xlim(0.5, study.OPERATING_BLOCKS + 0.5)
    ax.set_ylim(-0.025, 1.025)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.grid(alpha=0.2, linewidth=0.5)
    ax.set_axisbelow(True)
    # Put every legend entry outside the axes so no curve is obscured.
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.53, 1.0),
        ncol=2,
        frameon=False,
        fontsize=6.3,
        handlelength=1.7,
        columnspacing=0.8,
        handletextpad=0.4,
    )
    fig.subplots_adjust(left=0.16, right=0.985, bottom=0.19, top=0.79)
    fig.savefig(
        figures / "qber_cumulative_alerts.pdf",
        metadata={
            "Title": "Finite-horizon QBER monitoring: cumulative alert probabilities",
            "Author": "",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(figures / "qber_cumulative_alerts.png", dpi=300)
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parent
    results = root / "results" / "two_sample_monitoring_study"
    figures = root / "figures" / "two_sample_monitoring_study"
    summary_path = results / "two_sample_monitoring_summary.csv"
    if not summary_path.is_file():
        raise SystemExit(
            "Missing study summary. First run python -m research.two_sample_monitoring_study"
        )
    frame, calibration, retained_mass = compute_curves()
    verify_curves(frame, summary_path)
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    frame.to_csv(results / "poster_cumulative_alerts.csv", index=False)
    calibration.to_csv(results / "poster_calibration_thresholds.csv", index=False)
    draw_figure(frame, figures)
    config = {
        "figure_script_version": "1.0.0",
        "study_script_version": study.SCRIPT_VERSION,
        "calibration_bits": study.CALIBRATION_BITS,
        "sifted_length": study.SIFTED_LENGTH,
        "operating_blocks": study.OPERATING_BLOCKS,
        "baseline_qber": study.BASELINE_QBER,
        "interception_density": study.INTERCEPTION_DENSITY,
        "familywise_alpha": study.FAMILYWISE_ALPHA,
        "per_block_alpha": study.FAMILYWISE_ALPHA / study.OPERATING_BLOCKS,
        "calibration_tail_mass": study.CALIBRATION_TAIL_MASS,
        "retained_calibration_mass": retained_mass,
        "calculation": "Average 1-product(binomial CDFs) conditional on the shared calibration count",
        "verification": "All four final points match the saved study summary within 1e-11; matched paths agree at every block",
        "study_module_sha256": hashlib.sha256(Path(study.__file__).read_bytes()).hexdigest(),
        "summary_csv_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
    }
    (results / "poster_figure_config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    print("Figure reproduced; all final points agree with the saved run-level results.")
    final = frame[frame["operating_block"] == study.OPERATING_BLOCKS]
    for row in final.itertuples(index=False):
        print(f"{row.scenario_id}: {100 * row.cumulative_alert_probability:.3f}%")


if __name__ == "__main__":
    main()
