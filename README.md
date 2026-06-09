# Quantum-Safe Communication Explorer

Quantum-Safe Communication Explorer is a simulation and visualization project for studying BB84 Quantum Key Distribution, eavesdropping detection, QBER analysis, error correction, privacy amplification, channel noise, and message encryption using quantum-generated keys.

The project combines protocol-level BB84 simulation, Qiskit circuit demonstrations, repeated experiments, and an interactive Streamlit dashboard to show how quantum information principles can support secure communication.

## Live Demo

Try the interactive dashboard here:

[Launch Quantum-Safe Communication Explorer](https://quantum-safe-communication-explorer.streamlit.app/)

## Main Features

- BB84 Quantum Key Distribution simulation
- Eve intercept-resend attack model
- QBER experiment and visualization
- Message encryption using BB84-generated keys
- Parity-based error correction
- Privacy amplification using SHAKE-256 based final key derivation
- Channel noise simulation
- Eve vs channel noise comparison experiment
- Qiskit circuit-based BB84 demonstration
- Streamlit interactive dashboard
- Research-style project report

## Project Architecture

```text
User Input
   ↓
Streamlit Dashboard
   ↓
BB84 Protocol Simulator
   ↓
Eve Attack Model + Channel Noise Model
   ↓
QBER Calculation
   ↓
Parity-Based Error Correction
   ↓
Privacy Amplification / Final Key Derivation
   ↓
Message Encryption and Decryption
   ↓
Results, Graphs, and Dashboard Outputs
```

## Dashboard Preview

![Dashboard Preview](figures/dashboard_v0_5.png)

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

Run notebooks:

```bash
jupyter notebook
```

## Project Status

Current version: **v1.3**

The project currently supports BB84 simulation, Eve attack modeling, QBER experiments, parity-based error correction, privacy amplification, channel noise simulation, Eve-vs-noise comparison experiments, message encryption, Qiskit circuit demonstrations, project documentation, and a live deployed dashboard.

## Repository Structure

```text
quantum-safe-communication-explorer/
│
├── app.py
├── README.md
├── requirements.txt
│
├── src/
│   ├── bb84.py
│   ├── encryption.py
│   ├── error_correction.py
│   ├── experiments.py
│   ├── privacy_amplification.py
│   └── qiskit_bb84.py
│
├── notebooks/
│   ├── 01_bb84_basics.ipynb
│   ├── 02_eve_attack_simulation.ipynb
│   ├── 03_qber_experiments.ipynb
│   ├── 04_message_encryption.ipynb
│   ├── 05_qiskit_bb84_demo.ipynb
│   ├── 06_error_correction_demo.ipynb
│   ├── 07_privacy_amplification_demo.ipynb
│   ├── 08_channel_noise_demo.ipynb
│   └── 09_eve_noise_comparison.ipynb
│
├── figures/
├── results/
└── docs/
    └── project_report.md
```

## Technical Pipeline

The current communication pipeline is:

```text
BB84 key generation
→ QBER security check
→ parity-based error correction
→ privacy amplification
→ final key derivation
→ message encryption/decryption
```

The project also includes experiments that study how QBER changes under:

- increasing Eve interception probability
- increasing channel noise probability
- clean, noise-only, Eve-only, and Eve-plus-noise scenarios

## Key Results

### 1. Eve Interception Increases QBER

The intercept-resend attack introduces errors because Eve does not always measure in the same basis as Alice. The simulated QBER follows the expected approximate relationship:

```text
QBER ≈ Eve interception probability × 25%
```

### 2. Qiskit Confirms the BB84 Basis Rule

The Qiskit circuit demonstration confirms the core BB84 behavior:

```text
same basis → Bob recovers Alice's bit
different basis → Bob gets an approximately random result
```

### 3. Error Correction Is Needed Before Encryption

When QBER is low but nonzero, Alice and Bob may still have mismatched sifted keys. The parity-based correction step reduces these mismatches before the key is used.

### 4. Privacy Amplification Derives the Final Key

After correction, the reconciled key is compressed using a SHAKE-256 based derivation step. The derived final key is then used for message encryption.

### 5. QBER Can Come From Eve, Noise, or Both

The Eve-vs-noise comparison experiment shows that QBER can increase because of eavesdropping, channel noise, or a combination of both. This makes the simulator useful for studying both attack behavior and noisy transmission conditions.

## Output Files

Important generated outputs include:

```text
results/qber_experiment_results.csv
results/channel_noise_experiment_results.csv
results/eve_noise_comparison_results.csv

figures/qber_vs_eve_interception.png
figures/qber_vs_channel_noise.png
figures/eve_noise_comparison_qber.png
figures/qiskit_bb84_basis_results.png
```

## Version History

- v0.1: Implemented BB84 without eavesdropping
- v0.2: Added Eve intercept-resend attack simulation
- v0.3: Added QBER experiment and visualization
- v0.3.1: Fixed typo in QBER graph label
- v0.4: Added message encryption using the BB84-generated key
- v0.5: Added Streamlit interactive dashboard
- v0.6: Added Qiskit circuit-based BB84 demonstration
- v0.7: Added project report and improved README readability
- v0.8: Deployed the Streamlit dashboard and added live demo link
- v0.9: Added parity-based error correction
- v1.0: Added privacy amplification and final key derivation
- v1.1: Added channel noise simulation and QBER analysis
- v1.2: Added Eve vs channel noise comparison experiment
- v1.3: Refreshed README and project report for the full v1.2 pipeline

## Version 1.3: Documentation Refresh

This version updates the README and project report so they reflect the current full project pipeline.

### New Updates

- Rewrote the README for clarity and readability
- Updated the project architecture
- Added current pipeline description
- Added updated key results
- Added current repository structure
- Updated project report to include error correction, privacy amplification, channel noise, and Eve-vs-noise comparison
- Reduced repetitive warning language while keeping technical assumptions clear

### Output Files

- README.md
- docs/project_report.md

## Notes

This project is a simulation and research-style learning project. It is designed to explain and explore BB84-style quantum-safe communication concepts through code, experiments, and visualization.
