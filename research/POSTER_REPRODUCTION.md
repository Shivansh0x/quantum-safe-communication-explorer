# Reproduce the poster table and figure

Run these commands from the artifact root:

```bash
python -m pip install -r research/requirements-poster.txt
python -m research.two_sample_monitoring_study
python -m research.make_poster_figure
python -m unittest discover -s research/tests -v
```

`requirements-poster.txt` records the numerical package versions used for the
supplied results and figure. The existing suite contains 38 tests. The figure
command also checks all four
final plotted probabilities against the saved study summary, verifies that
the matched benign and attack curves agree at every block, checks that each
curve is a nondecreasing probability, and checks the stationary error budget.

If the study summary already exists, the figure command can be run directly.

## Files

- Table 1: `results/two_sample_monitoring_study/two_sample_monitoring_summary.csv`
- Figure 1, vector PDF: `figures/two_sample_monitoring_study/qber_cumulative_alerts.pdf`
- Figure 1, PNG preview: `figures/two_sample_monitoring_study/qber_cumulative_alerts.png`
- All 80 plotted values: `results/two_sample_monitoring_study/poster_cumulative_alerts.csv`
- Calibration weights and critical counts: `results/two_sample_monitoring_study/poster_calibration_thresholds.csv`
- Parameters, numerical versions and provenance hashes: `results/two_sample_monitoring_study/poster_figure_config.json`

These paths are relative to `research/`. `make_poster_figure.py` imports the
existing study module; it does not redefine the test or change the scenarios.

## Calculation

The two-sample per-block level is 0.01 / 20 = 0.0005. For each retained
calibration error count, the script uses the study's smallest rejected
operating count. It computes the product of the binomial no-alert
probabilities through each operating block, subtracts that product from one,
and only then averages over the calibration count. Taking the product after
averaging would incorrectly treat the repeated tests as independent.

The calibration sum retains more than 1 - 1e-12 of its binomial mass; retained
weights are normalized. Curves are numerical evaluations of analytical
probabilities, with ordinary floating-point error, not Monte Carlo estimates.
There is no random seed for this calculation because it uses no random draws.

Final two-sample probabilities, in percent:

| Scenario | Alert by operating block 20 |
| --- | ---: |
| Stationary, no change | 0.714 |
| Gradual benign drift | 93.007 |
| Matched benign step | 99.928 |
| 10% intercept-resend | 99.928 |

Only the stationary row measures false alarms under the no-change null.
The other rows measure sensitivity to increased QBER. Equal matched curves
reflect identical joint count laws in the independent Bernoulli model; they
do not demonstrate an ability to identify an attack.
