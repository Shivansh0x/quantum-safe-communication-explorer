# Baseline-Miscalibration Research Workspace

This directory keeps the research experiments separate from the educational
application. The paper itself should be written independently; these files store
code, data, figures, and a dated decision log.

## Checkpoint 1: validate the QBER model

Run a quick smoke test first:

```bash
python -m unittest research.tests.test_model_validation
```

Then run the preregistered model-validation grid:

```bash
python -m research.model_validation
```

The command creates:

```text
research/results/model_validation/model_validation_trials.csv
research/results/model_validation/model_validation_summary.csv
```

The trial file is the primary output. It retains the error count, sifted-key
length, and random seed for every run. The summary file is derived from it.

Before inspecting the results, complete the prediction prompts in
`research/research_log.md`. Afterward, record what the output supports and what
remains unresolved.

## Planned checkpoints

1. Validate the exact expected-QBER model.
2. Implement a fixed-baseline binomial detector.
3. Verify its nominal false-positive rate when correctly calibrated.
4. Sweep assumed-versus-actual baseline mismatch.
5. Measure false-positive rate, false-negative rate, power, and estimator bias.
6. Repeat across finite sifted-key lengths.
7. Generate final figures and robustness tables.

