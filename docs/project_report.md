# Quantum-Safe Communication Explorer

## Abstract

Quantum-Safe Communication Explorer studies BB84 Quantum Key Distribution through simulation, experimentation, visualization, and circuit-level validation. The project models key generation between Alice and Bob, Eve's intercept-resend attack, channel noise, QBER analysis, parity-based error correction, privacy amplification, and message encryption using derived keys. It also includes Qiskit-based circuit demonstrations and an interactive Streamlit dashboard.

The project is designed as an exploration of how quantum information principles can support secure communication and how QBER changes under clean, noisy, attacked, and combined channel conditions.

## 1. Motivation

Modern digital communication depends on cryptographic systems for confidentiality and trust. Future large-scale quantum computers may weaken some widely used public-key systems, which makes quantum-safe communication an important area of study.

This project focuses on BB84, one of the earliest and most important quantum key distribution protocols. The goal is to understand how quantum states can be used to generate shared keys, how eavesdropping creates detectable disturbance, and how additional steps such as error correction and privacy amplification are needed before using the generated key.

## 2. Background

### 2.1 Quantum Key Distribution

Quantum Key Distribution allows two parties to generate a shared key using quantum states and classical communication. BB84 uses two measurement bases:

- Z basis: computational basis
- X basis: diagonal basis

Alice randomly chooses bits and bases. Bob independently chooses measurement bases. After transmission, they publicly compare bases and keep only the positions where their bases matched.

### 2.2 Quantum Bit Error Rate

The Quantum Bit Error Rate measures the fraction of mismatched bits between Alice and Bob's sifted keys.

A high QBER can indicate:

- eavesdropping
- channel noise
- imperfect transmission
- measurement disturbance

In this project, QBER is used as the central metric for deciding whether communication should continue or abort.

### 2.3 Intercept-Resend Attack

The intercept-resend attack is a simple eavesdropping strategy. Eve intercepts some transmitted qubits, measures them using randomly selected bases, and resends the measured result to Bob.

Because Eve does not always choose the correct basis, her measurement can disturb the state. This disturbance increases QBER.

For an intercept-resend attack, the expected approximate relationship is:

```text
QBER ≈ Eve interception probability × 25%
```

### 2.4 Error Correction

Even when QBER is below the selected threshold, Alice and Bob's sifted keys may still contain mismatched bits. This project implements a parity-based correction method to reduce mismatches before encryption.

The correction method uses:

- block parity checks
- binary parity search for likely error positions
- multiple shuffled passes
- final mismatch tracking

### 2.5 Privacy Amplification

After error correction, the reconciled key is compressed into a shorter final key. This project uses a SHAKE-256 based key derivation step for privacy amplification and final key generation.

The current pipeline is:

```text
Raw BB84 key
→ error correction
→ privacy amplification
→ final key
```

### 2.6 Channel Noise

Real communication channels may introduce errors even when no attacker is present. This project includes a simple bit-flip channel noise model so that QBER can be studied under clean, noisy, attacked, and combined scenarios.

## 3. System Design

The project is organized into separate modules:

```text
src/bb84.py                  BB84 simulation and channel noise model
src/encryption.py            Message encryption and full exchange pipeline
src/error_correction.py      Parity-based correction
src/privacy_amplification.py Final key derivation
src/experiments.py           QBER experiments
src/qiskit_bb84.py           Qiskit circuit-based BB84 demo
app.py                       Streamlit dashboard
```

The full communication pipeline is:

```text
Alice bit and basis generation
→ Bob basis generation
→ Eve intercept-resend model
→ channel noise model
→ basis sifting
→ QBER calculation
→ parity-based correction
→ privacy amplification
→ message encryption/decryption
```

## 4. Implementation

### 4.1 BB84 Protocol Simulation

The protocol-level simulator follows the core BB84 rule:

```text
same basis → Bob gets Alice's bit
different basis → Bob gets a random bit
```

This allows the project to simulate large numbers of qubits efficiently and study QBER trends across repeated trials.

### 4.2 Eve Attack Model

Eve intercepts each qubit with a configurable probability. When she intercepts, she randomly chooses a basis, measures the qubit, and resends her result to Bob.

This allows the project to study how increasing Eve's interception probability affects QBER.

### 4.3 Channel Noise Model

The channel noise model flips transmitted bits with a configurable probability. This creates errors even when Eve is absent.

This makes it possible to compare:

- clean communication
- noise-only communication
- Eve-only communication
- Eve plus channel noise

### 4.4 Message Encryption

After a final key is derived, the project converts the input message into bits and encrypts it using XOR-based bit encryption. Bob decrypts using his derived key.

This demonstrates how a BB84-generated key can be connected to message transmission after QBER checks, correction, and final key derivation.

### 4.5 Qiskit Circuit Demonstration

The Qiskit notebook prepares the four BB84 states:

- bit 0 in Z basis: |0>
- bit 1 in Z basis: |1>
- bit 0 in X basis: |+>
- bit 1 in X basis: |->

Bob then measures in either the Z or X basis. The circuit results confirm that same-basis measurements are deterministic while different-basis measurements are approximately random.

## 5. Experiments

### 5.1 QBER vs Eve Interception

The first experiment varies Eve's interception probability from 0% to 100% and measures average QBER across repeated trials.

The result follows the expected approximate relationship:

```text
QBER ≈ Eve interception probability × 25%
```

### 5.2 Qiskit Basis Demonstration

The Qiskit experiment runs all BB84 bit and basis combinations. It confirms:

```text
same basis → deterministic result
different basis → approximately random result
```

This validates the simplified protocol-level rule used in the main simulator.

### 5.3 Error Correction Demonstration

The error correction notebook shows that low QBER does not always mean Alice and Bob's keys are already identical. The parity-based correction step reduces raw mismatches and prepares the key for final derivation.

### 5.4 Privacy Amplification Demonstration

The privacy amplification notebook shows how the reconciled key can be compressed into a shorter final key using SHAKE-256 based derivation. The final key is then used for message encryption.

### 5.5 Channel Noise Experiment

The channel noise experiment varies the noise probability and measures how QBER changes when Eve is absent. As the noise probability increases, QBER also increases.

### 5.6 Eve vs Channel Noise Comparison

The comparison experiment studies four scenarios:

1. Clean channel
2. Noise only
3. Eve only
4. Eve + noise

This helps separate errors caused by ordinary channel noise from errors caused by eavesdropping.

## 6. Results

The project produces several important results.

### 6.1 Eavesdropping Increases QBER

The intercept-resend model shows that QBER rises as Eve intercepts more qubits. This supports the central BB84 idea that measurement disturbance can reveal eavesdropping.

### 6.2 QBER Alone Does Not Identify the Cause

Channel noise can also raise QBER. The Eve-vs-noise comparison shows that a high QBER indicates a problem, but not necessarily whether the problem is an attacker, noise, or both.

### 6.3 Error Correction Is Needed Before Encryption

When QBER is low but nonzero, Alice and Bob may still have mismatched raw keys. The correction step reduces these mismatches before privacy amplification and encryption.

### 6.4 Privacy Amplification Completes the Key Pipeline

The final key derivation step compresses the reconciled key before encryption. This makes the simulation pipeline more complete and closer to the structure of a BB84-style communication workflow.

### 6.5 Qiskit Connects the Protocol to Quantum Circuits

The Qiskit demonstration shows that the simplified simulation rule is grounded in actual one-qubit circuit behavior.

## 7. Dashboard

The Streamlit dashboard allows users to adjust:

- number of BB84 qubits
- Eve interception probability
- channel noise probability
- QBER threshold
- error-correction settings
- privacy amplification settings
- message input

The dashboard displays:

- communication status
- QBER
- key lengths
- raw and final mismatches
- correction metrics
- final key fingerprint
- ciphertext and decrypted message
- QBER experiment graphs

The deployed dashboard makes the project easier to explore without running the notebooks manually.

## 8. Limitations

The current project is a simulation. Important limitations include:

- no real quantum hardware channel
- simple bit-flip channel noise model
- parity-based correction rather than a full production reconciliation protocol
- XOR-based message encryption for demonstration
- no full authentication layer
- no deployment of real cryptographic key management
- no hardware noise calibration

These limitations are useful future directions rather than flaws in the current learning-focused design.

## 9. Future Work

Possible next steps include:

- stronger error-correction experiments
- Qiskit Aer noise models
- IBM Quantum hardware runs
- comparison with entanglement-based QKD
- AES-based message encryption demo
- a blog series explaining the full BB84 pipeline
- expanded dashboard controls for experiment generation

## 10. Conclusion

Quantum-Safe Communication Explorer demonstrates the BB84 communication pipeline through simulation, experiments, circuit validation, and interactive visualization.

By combining BB84 key generation, Eve attack modeling, QBER analysis, parity-based correction, privacy amplification, channel noise, Qiskit circuits, and dashboard deployment, the project connects quantum information and cryptography in one coherent system.
