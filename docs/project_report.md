# Quantum-Safe Communication Explorer

This report reflects the v2.0 release of the project, including BB84 simulation, QBER analysis, error correction, privacy amplification, Qiskit simulation, IBM Quantum hardware results, and dashboard deployment.

## Abstract

Quantum-Safe Communication Explorer is a simulation, experimentation, and visualization project for studying BB84 Quantum Key Distribution. The project models key generation between Alice and Bob, Eve's intercept-resend attack, channel noise, Quantum Bit Error Rate analysis, parity-based error correction, privacy amplification, message encryption, Qiskit circuit simulation, Qiskit Aer noise models, and selected IBM Quantum hardware runs.

The project is designed to connect quantum information, cryptography, probability, computer science, and interactive visualization in one coherent system. It begins with a basic BB84 simulator and develops into a broader BB84 analysis platform with experiments, graphs, notebooks, and a deployed Streamlit dashboard.

## 1. Motivation

Modern secure communication depends on reliable key exchange. Many widely used public-key cryptographic systems may face future threats from large-scale quantum computers, making quantum-safe communication an important area of study.

BB84 is one of the earliest and most important quantum key distribution protocols. It demonstrates how quantum measurement can be used not only to generate shared keys, but also to detect disturbance caused by eavesdropping.

The goal of this project is to understand BB84 by building it from the ground up:

```text
basic key generation
→ eavesdropping simulation
→ QBER analysis
→ error correction
→ privacy amplification
→ message encryption
→ noisy simulation
→ hardware-backed experiments
```

Rather than only reading about BB84 conceptually, this project implements the protocol, runs experiments, visualizes results, and connects the protocol-level model to Qiskit circuits and IBM Quantum hardware.

## 2. Background

### 2.1 Quantum Key Distribution

Quantum Key Distribution allows two parties, usually called Alice and Bob, to generate a shared secret key using quantum states and classical communication.

In BB84, Alice randomly prepares bits using one of two bases:

- Z basis
- X basis

Bob independently chooses measurement bases. After transmission, Alice and Bob publicly compare only their bases, not their secret bit values. They keep the positions where their bases matched and discard the rest. The remaining bits form the sifted key.

### 2.2 BB84 Basis Behavior

The core BB84 rule is:

```text
same basis → Bob recovers Alice's bit
different basis → Bob receives an approximately random result
```

This rule is simulated directly in the protocol-level BB84 model and later validated using Qiskit circuits.

### 2.3 Quantum Bit Error Rate

The Quantum Bit Error Rate is the fraction of mismatched bits between Alice and Bob's sifted keys.

```text
QBER = mismatched sifted bits / total compared sifted bits
```

QBER is important because it indicates whether the channel is clean, noisy, or possibly disturbed by eavesdropping.

A high QBER can be caused by:

- Eve's intercept-resend attack
- normal channel noise
- imperfect quantum gates
- measurement error
- hardware noise
- a combination of these factors

### 2.4 Eve's Intercept-Resend Attack

In the intercept-resend attack, Eve intercepts some transmitted qubits, measures them using randomly selected bases, and resends her measured result to Bob.

If Eve chooses the wrong basis, she can disturb the state. This disturbance creates mismatches between Alice and Bob's sifted keys.

For a simple intercept-resend attack, the expected approximate relationship is:

```text
QBER ≈ Eve interception probability × 25%
```

### 2.5 Error Correction

Even when QBER is below the selected threshold, Alice and Bob's sifted keys may still contain mismatches. If these mismatches remain, message decryption may fail.

This project implements a parity-based error correction method that uses:

- block parity checks
- binary parity search
- multiple shuffled correction passes
- final mismatch tracking

The goal is to reduce or eliminate mismatches before the key is used.

### 2.6 Privacy Amplification

After error correction, the reconciled key is compressed into a shorter final key using a SHAKE-256 based derivation step.

This project uses privacy amplification to model the final key derivation stage of a BB84-style communication pipeline.

The simplified key-processing pipeline is:

```text
raw sifted key
→ error correction
→ privacy amplification
→ final derived key
```

### 2.7 Channel and Hardware Noise

Real communication systems are not perfect. Errors can appear even when there is no eavesdropper.

This project studies noise in three layers:

1. Protocol-level channel noise
2. Qiskit Aer circuit-level noise
3. IBM Quantum hardware noise

This makes it possible to compare ideal behavior, noisy simulation, and real-device results.

## 3. System Design

The project is organized into separate modules:

```text
src/bb84.py                              BB84 simulation and channel noise model
src/encryption.py                        Full message exchange pipeline
src/error_correction.py                  Parity-based error correction
src/error_correction_experiments.py      Error correction parameter sweep
src/privacy_amplification.py             Final key derivation
src/privacy_amplification_experiments.py Privacy amplification parameter sweep
src/experiments.py                       QBER and noise experiments
src/qiskit_bb84.py                       Qiskit BB84 circuit demo
src/qiskit_noise.py                      Qiskit Aer noise model experiment
src/ibm_hardware.py                      IBM Quantum hardware integration
app.py                                   Streamlit dashboard
```

The main communication pipeline is:

```text
Alice bit and basis generation
→ Bob basis generation
→ Eve intercept-resend model
→ channel noise model
→ basis sifting
→ QBER calculation
→ parity-based error correction
→ privacy amplification
→ final key derivation
→ message encryption/decryption
```

The circuit and hardware layer is:

```text
BB84 circuit construction
→ ideal Qiskit simulation
→ Qiskit Aer noisy simulation
→ IBM Quantum hardware run
→ circuit-level result comparison
```

## 4. Implementation

### 4.1 Protocol-Level BB84 Simulation

The protocol-level simulator generates Alice's random bits and bases, Bob's random bases, and Bob's measurement outcomes.

When Alice and Bob use the same basis, Bob receives Alice's bit. When their bases differ, Bob's result is random.

This model allows the project to efficiently simulate thousands of BB84 transmissions and run repeated experiments.

### 4.2 Eve Attack Model

The Eve model uses an intercept-resend attack. Eve intercepts each qubit with a selected probability. When she intercepts, she chooses a random basis, measures the qubit, and resends the measured result to Bob.

This allows the project to study how increasing Eve's interception probability affects QBER.

### 4.3 Channel Noise Model

The channel noise model flips transmitted bits with a selected probability. This creates errors even when Eve is absent.

The noise model allows the project to compare:

- clean channel behavior
- noise-only behavior
- Eve-only behavior
- Eve plus noise behavior

### 4.4 Message Encryption

After BB84 key generation, QBER checking, correction, and privacy amplification, the final derived key is used to encrypt a message.

The project uses XOR-based bit encryption to demonstrate how a generated key can be applied to message transmission. The purpose is to connect BB84 key generation to a complete communication flow.

### 4.5 Error Correction

The parity-based error correction step divides the key into blocks and compares parities. If a parity mismatch is detected, a binary parity search is used to locate a likely error position, and Bob's bit is flipped.

This process is repeated across several shuffled passes.

The module tracks:

- raw mismatches
- final mismatches
- corrections applied
- parity checks
- correction success

### 4.6 Privacy Amplification

The privacy amplification module converts reconciled key bits into bytes and uses SHAKE-256 to derive a final key of the required length.

The project also tracks the effect of compression ratio on final key capacity and message success.

### 4.7 Qiskit Circuit Demonstration

The Qiskit BB84 module creates one-qubit BB84 circuits for the four BB84 states:

- bit 0 in Z basis: |0>
- bit 1 in Z basis: |1>
- bit 0 in X basis: |+>
- bit 1 in X basis: |->

Bob then measures in either the Z or X basis. The results confirm the same-basis and different-basis behavior used in the protocol simulator.

### 4.8 Qiskit Aer Noise Models

The Qiskit Aer noise module adds circuit-level noise using depolarizing gate noise and readout error.

This experiment compares ideal BB84 circuits with noisy BB84 circuits and shows how circuit noise increases wrong measurement probability.

### 4.9 IBM Quantum Hardware Demonstration

The IBM Quantum hardware module runs selected BB84 circuits on real IBM Quantum hardware.

The hardware demo includes:

- backend selection
- circuit transpilation
- IBM Runtime integration
- selected BB84 circuit execution
- result collection
- hardware comparison graph

This connects the project to real quantum devices and shows how real hardware differs from ideal simulation.

### 4.10 Streamlit Dashboard

The Streamlit dashboard provides an interactive interface for running the BB84 communication pipeline.

The dashboard includes:

- live protocol simulation
- QBER experiment graphs
- circuit and hardware graphs
- key-processing experiment graphs
- technical notes

The dashboard is organized into tabs so users can explore the project without scrolling through every result at once.

## 5. Experiments

### 5.1 QBER vs Eve Interception

This experiment varies Eve's interception probability from 0% to 100% and measures the average QBER across repeated trials.

The simulation follows the expected approximate relationship:

```text
QBER ≈ Eve interception probability × 25%
```

### 5.2 Qiskit BB84 Basis Demonstration

This experiment runs all combinations of Alice bit, Alice basis, and Bob basis.

The result confirms:

```text
same basis → deterministic result
different basis → approximately random result
```

### 5.3 Message Encryption Demo

This experiment connects BB84 key generation to message encryption.

The system checks QBER, applies key processing, derives a final key, encrypts the message, and attempts to decrypt it with Bob's key.

If the channel is too noisy or the key material is insufficient, communication is aborted.

### 5.4 Error Correction Demonstration

This experiment shows why correction is needed when QBER is low but nonzero.

Even a small mismatch rate can cause decryption failure. The parity-based correction step reduces mismatches before privacy amplification.

### 5.5 Privacy Amplification Demonstration

This experiment shows how the reconciled key is compressed into a final derived key.

The derived key is then used for message encryption and decryption.

### 5.6 Channel Noise Experiment

This experiment varies channel noise probability while Eve is absent.

As channel noise increases, QBER also increases. This shows that errors can arise even without an attacker.

### 5.7 Eve vs Channel Noise Comparison

This experiment compares four scenarios:

1. Clean channel
2. Noise only
3. Eve only
4. Eve + noise

The result shows that QBER can be caused by Eve, noise, or both.

### 5.8 Qiskit Aer Noise Experiment

This experiment compares ideal BB84 circuits with noisy Qiskit Aer circuits.

As gate and readout noise increase, the probability of a wrong measurement increases.

### 5.9 IBM Quantum Hardware Experiment

This experiment runs selected BB84 circuits on IBM Quantum hardware.

Same-basis circuits should mostly recover Alice's bit. Different-basis circuits should be closer to random. Real hardware introduces deviations from ideal simulation.

### 5.10 Error Correction Parameter Sweep

This experiment varies:

- block size
- correction passes

It measures:

- success rate
- average raw mismatches
- average final mismatches
- corrections applied
- parity checks

The goal is to understand the tradeoff between correction reliability and correction cost.

### 5.11 Privacy Amplification Parameter Sweep

This experiment varies:

- privacy compression ratio
- message length

It measures:

- message success rate
- final key capacity
- insufficient-key failures
- QBER failures
- mismatch failures

The goal is to understand the tradeoff between compression strength and usable key material.

## 6. Results

### 6.1 Eavesdropping Increases QBER

The intercept-resend model shows that QBER rises as Eve intercepts more qubits.

This supports the central BB84 idea that measurement disturbance can reveal possible eavesdropping.

### 6.2 Channel Noise Also Increases QBER

The channel noise experiment shows that QBER can increase even when Eve is absent.

This means QBER is not only an eavesdropping signal. It is also affected by transmission noise.

### 6.3 QBER Is a Warning Signal, Not a Complete Diagnosis

The Eve-vs-noise comparison shows that QBER can be caused by eavesdropping, noise, or both.

A high QBER tells Alice and Bob that the channel is disturbed, but it does not identify the exact cause of the disturbance.

### 6.4 Qiskit Confirms the Basis Behavior

The Qiskit circuit demonstration confirms that same-basis measurements recover Alice's bit while different-basis measurements are approximately random.

This validates the simplified rule used in the protocol-level simulator.

### 6.5 Qiskit Aer Connects Protocol Noise to Circuit Noise

The Qiskit Aer noise experiment shows that circuit-level gate and readout noise can increase wrong measurement probability.

This connects the protocol-level bit-flip model to noisy quantum circuit simulation.

### 6.6 IBM Hardware Shows Real Device Imperfections

The IBM Quantum hardware demonstration shows that real quantum devices deviate from ideal simulation.

This adds a practical hardware-backed layer to the project.

### 6.7 Error Correction Has a Reliability-Cost Tradeoff

The error correction parameter sweep shows that increasing correction passes can improve success rate, but also increases the number of parity checks.

This demonstrates the tradeoff between reliability and communication cost.

### 6.8 Privacy Amplification Has a Compression-Capacity Tradeoff

The privacy amplification parameter sweep shows that stronger compression reduces final key length, while weaker compression preserves more usable key capacity.

This demonstrates a tradeoff between compression and message capacity.

## 7. Dashboard

The dashboard is organized into five sections:

1. Live Simulation
2. QBER Experiments
3. Circuit + Hardware
4. Key Processing
5. Technical Notes

The live simulation allows users to control:

- number of BB84 qubits
- Eve interception probability
- channel noise probability
- QBER threshold
- error correction settings
- privacy amplification settings
- message input

The saved experiment tabs display graphs generated from notebooks.

IBM Quantum hardware jobs are run from notebooks, not from the public dashboard.

## 8. Limitations

This project is a simulation and analysis platform. Important limitations include:

- no real-time quantum hardware execution from the dashboard
- XOR-based message encryption for demonstration
- no full authentication layer
- no real-world key management system
- small-scale IBM Quantum hardware experiments rather than large hardware benchmarking
- no comparison with entanglement-based QKD yet

These limitations are natural future directions for the project.

## 9. Future Work

The v2.0 release completes the main BB84 simulation and analysis pipeline. Optional future extensions include:

- more IBM Quantum hardware runs
- comparison with E91 entanglement-based QKD
- BB84 vs E91 comparison
- expanded attack models
- stronger reconciliation experiments
- deeper privacy amplification analysis
- public technical articles explaining the project

## 10. Conclusion

Quantum-Safe Communication Explorer demonstrates a BB84-inspired quantum-safe communication pipeline through simulation, experiments, visualization, Qiskit circuits, Qiskit Aer noise models, and IBM Quantum hardware runs.

The project shows how eavesdropping and noise affect QBER, why error correction and privacy amplification are needed, how circuit-level and hardware-level noise differ from ideal behavior, and how a generated key can be used for message encryption.

By combining quantum information, cryptography, probability, Python programming, Qiskit, IBM Quantum hardware, and Streamlit deployment, the project forms a complete research-style exploration of BB84 quantum key distribution.
