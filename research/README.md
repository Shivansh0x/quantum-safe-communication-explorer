# Baseline-QBER Mismatch Research

This directory contains the reproducible experiments used to study how
incorrect baseline-QBER assumptions affect a simplified BB84 QBER anomaly
detector.

The research code is kept separate from the educational Streamlit application
in the repository root.

## Research question

A QBER-based detector must distinguish attack-induced errors from ordinary
channel noise. In practice, the detector may be calibrated using an assumed
baseline QBER that differs from the channel's actual no-attack QBER.

This study asks:

1. How does baseline-QBER mismatch affect false-positive and false-negative
   probabilities?
2. How does mismatch bias an estimator of Eve's interception density?
3. Does increasing the number of examined sifted bits correct baseline
   miscalibration?
4. Can an uncertainty-aware threshold control false positives when the baseline
   is only known to lie within a bounded range?

## Simplified model

The study models partial intercept-resend attacks against BB84.

| Symbol | Meaning |
|---|---|
| $b_a$ | Assumed baseline channel-error probability used to calibrate the detector |
| $b_t$ | Actual channel-error probability |
| $\delta=b_t-b_a$ | Baseline mismatch |
| $p$ | Probability that Eve intercepts each transmitted qubit |
| $K$ | Number of sifted bits examined for QBER estimation |
| $X$ | Number of disagreements among the $K$ examined bits |
| $\widehat q=X/K$ | Measured QBER |
| $\alpha$ | Target false-positive probability |
| $u$ | Upward baseline-uncertainty margin |

Within the independent bit-flip and random-basis partial intercept-resend model,
the expected QBER is

$$
q(b_t,p) = b_t + p\left(\frac{1}{4}-\frac{b_t}{2}\right).
$$

The interaction term accounts for the way channel noise and Eve's disturbance
combine in the implemented simulator. The simpler additive approximation is

$$
q_{\mathrm{add}}(b_t,p) = b_t+\frac{p}{4}.
$$

Their difference is

$$
q_{\mathrm{add}}-q = \frac{b_t p}{2}.
$$

The detector estimates interception density using its assumed baseline:

$$
\widehat p =
\frac{\widehat q-b_a}
{\frac{1}{4}-\frac{b_a}{2}}.
$$

For the raw, unclipped estimator, baseline mismatch produces analytical bias

$$
\mathrm{Bias}(\widehat p) =
\frac{
\delta\left(1-\frac{p}{2}\right)
}{
\frac{1}{4}-\frac{b_a}{2}
}.
$$

These equations are exact only within the simplified independent-error model
used by this project. They are not a complete physical model or security proof
of a deployed QKD system.

## Detector definitions

### Fixed-baseline detector

Under the detector's assumed no-attack model,

$$
X\sim\mathrm{Binomial}(K,b_a).
$$

The critical count is the smallest integer $c$ satisfying

$$
\Pr(X\ge c\mid b_a)\le\alpha.
$$

The detector raises an alarm when $X\ge c$.

### Uncertainty-aware detector

To cover bounded upward baseline variation, the detector uses

$$
b_U=b_a+u
$$

and calibrates its critical count at $b_U$.

Under the model assumptions, this gives the conditional guarantee

$$
b_t\le b_a+u
\quad\Longrightarrow\quad
\mathrm{FPR}(b_t;K,u)\le\alpha.
$$

A larger uncertainty margin reduces false alarms over a wider baseline range,
but it also reduces sensitivity to weak attacks.

## Experiments

The directory contains five experiments.

### 1. Expected-QBER model validation

Module:

```text
research/model_validation.py
```

This experiment compares the interaction-aware and additive expected-QBER
equations with the protocol-level BB84 simulator.

The principal grid contains:

- four channel-noise probabilities;
- three interception densities;
- 200 trials per condition; and
- 5,000 transmitted raw qubits per trial.

### 2. Fixed-baseline detector study

Module:

```text
research/detector_study.py
```

This experiment evaluates fixed-baseline detection and interception-density
estimation across:

- nine actual baselines;
- five interception densities;
- five sifted sample sizes;
- 20,000 trials per condition; and
- a target false-positive probability of 1%.

Because the independent-error model gives a binomial error count, this
experiment samples error counts directly instead of repeatedly running the
slower protocol-level simulator.

### 3. Uncertainty-aware detector study

Module:

```text
research/robust_detector_study.py
```

This experiment repeats the detector grid using uncertainty margins of 0, 0.5,
1, and 2 QBER percentage points.

It checks the false-positive guarantee for every no-attack condition lying
within the declared uncertainty range and measures the corresponding loss of
attack-detection power.

### 4. Protocol-level cross-validation

Module:

```text
research/full_bb84_validation.py
```

This experiment compares the direct-binomial calculations with the original
bit-level BB84 simulator.

Each trial collects exactly $K$ sifted bits before calculating QBER and applying
the detector threshold.

### 5. Data-driven uncertainty margin

Module:

```text
research/calibration_budget_study.py
```

The fixed uncertainty margin `u` in experiment 3 is chosen by hand, which
relocates rather than solves the calibration problem. This experiment derives
the margin from a no-attack calibration period of `N_cal` sifted bits using a
one-sided Clopper-Pearson upper confidence bound at level `1 - beta`:

$$
b_U = \mathrm{CP}_\beta(X_{\mathrm{cal}}, N_{\mathrm{cal}}).
$$

Because Clopper-Pearson covers `b_t` with probability at least `1 - beta`, and
because the binomial upper tail is nondecreasing in its success probability,
the unconditional no-attack alarm probability of the resulting detector is at
most `alpha + beta`, provided the channel is stationary between the two blocks.

The grid contains:

- six calibration budgets from 1,000 to 100,000 sifted bits;
- two calibration levels, `beta = 0.01` and `beta = 0.001`;
- four interception densities; and
- 40,000 trials per condition, for 48 conditions and 1.92 million trials.

It measures the realised margin, the false-alarm probability, and detection
power as a function of the calibration budget, against an oracle detector that
knows `b_t` exactly.

Processed data are written to `research/results/calibration_budget_study/` and
plots to `research/figures/calibration_budget_study/`, following the same
layout as the other research modules.


## Directory structure

```text
research/
├── calibration_budget_study.py
├── detector_study.py
├── full_bb84_validation.py
├── model_validation.py
├── robust_detector_study.py
├── requirements.txt
├── README.md
├── tests/
├── results/
│   ├── model_validation/
│   ├── detector_study/
│   ├── robust_detector_study/
│   ├── full_bb84_validation/
│   └── calibration_budget_study/
└── figures/
    ├── detector_study/
    ├── calibration_budget_study/
    ├── robust_detector_study/
    └── full_bb84_validation/
```

Smoke-test outputs and private paper-development files are intentionally
excluded from version control.

## Installation

Run the following commands from the repository root.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it using the command appropriate for your operating system, then
install the research dependencies:

```bash
python -m pip install -r research/requirements.txt
```

## Running the tests

Run the complete research test suite from the repository root:

```bash
python -m unittest discover -s research/tests -v
```

The current suite contains 30 tests covering:

- analytical boundary cases;
- invalid parameters;
- exact collection of $K$ sifted bits;
- threshold minimality;
- Wilson intervals;
- experiment grid sizes;
- deterministic seed uniqueness;
- monotonicity of uncertainty-aware thresholds;
- false-positive control within the declared uncertainty bound;
- Clopper-Pearson upper-bound behavior;
- the conditional false-positive guarantee at every baseline within bound; and
- expected-QBER boundary cases.

## Reproducing the experiments

Run the experiments from the repository root in the following order:

```bash
python -m research.model_validation
python -m research.detector_study
python -m research.robust_detector_study
python -m research.full_bb84_validation
python -m research.calibration_budget_study
```

The commands write processed data to `research/results/` and plots to
`research/figures/`.

The main-study master seeds are:

| Experiment | Master seed |
|---|---:|
| Expected-QBER model validation | 2026 |
| Fixed-baseline detector study | 2026 |
| Uncertainty-aware detector study | 2027 |
| Protocol-level BB84 cross-validation | 2028 |
| Data-driven uncertainty margin | 2029 |

Configuration JSON files preserve the grids, seeds, script versions, and
relevant software information used for the saved results.

## Principal results

The saved experiments support the following findings:

1. Across the 12 expected-QBER validation conditions, the interaction-aware
   equation had a mean absolute discrepancy of approximately 0.0179 QBER
   percentage points. The additive approximation had a discrepancy of
   approximately 0.1242 percentage points.

2. Positive baseline mismatch can produce severe false alarms. With an assumed
   baseline of 3% and an actual baseline of 5%, the fixed detector's theoretical
   no-attack alarm probability increased from approximately 27.12% at $K=250$
   to 82.67% at $K=1000$ and nearly 100% at $K=5000$.

3. Negative baseline mismatch can hide weak attacks. Increasing $K$ reduces
   sampling variation, but it does not correct a wrongly calibrated baseline.

4. All 135 tested no-attack conditions lying within their declared uncertainty
   ranges satisfied the theoretical 1% false-positive bound.

5. The protocol-level simulator closely reproduced the analytical expected-QBER
   predictions. All 36 exact alarm probabilities fell within
   their corresponding empirical 95% Wilson intervals.

6. Deriving the uncertainty margin from a calibration period makes the
   calibration budget an explicit design parameter. At K = 1000 and
   alpha = beta = 0.01, raising the budget from 1,000 to 25,000 sifted bits
   lifts detection power against a 10% interception attack from roughly 23% to
   82%, against an oracle ceiling of 92.3%, while every no-attack alarm rate
   stays well below the alpha + beta bound.

## Interpretation

Increasing $K$ improves statistical precision, but it does not determine
whether the assumed baseline is correct. When the model is miscalibrated, a
larger sample can make the detector more consistently follow the wrong decision
boundary.

The uncertainty-aware detector addresses bounded upward baseline variation by
calibrating at an upper baseline. This produces a transparent false-positive
guarantee within the covered range, but it requires a higher threshold and
therefore reduces detection power against weak attacks.

## Limitations

This is a simplified statistical study rather than a complete QKD security
analysis.

The model assumes:

- ideal single-qubit preparation and measurement;
- authenticated classical communication;
- independent Bernoulli channel-error events;
- constant channel noise within each experimental condition;
- independent random-basis partial intercept-resend attacks;
- no photon loss or dark counts;
- no multiphoton pulses;
- no detector or source side channels;
- no adaptive attacker;
- a stationary baseline between the calibration and operating blocks;
- no error correction or privacy amplification in the detector analysis; and
- no finite-key secret-rate calculation.

A QBER alarm identifies inconsistency with an assumed baseline model. It does
not uniquely prove that Eve caused the observed errors.

## Relationship to the main project

The main repository is an educational quantum-safe communication explorer
containing BB84 simulation, QBER experiments, error correction, privacy
amplification, Qiskit demonstrations, and a Streamlit interface.

This research directory focuses specifically on statistical calibration and
robustness of the QBER-based detection component.
