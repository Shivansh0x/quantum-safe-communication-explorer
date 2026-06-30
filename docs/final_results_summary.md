# Final Results Summary

## Overview

This document summarizes the main results from the Quantum-Safe Communication Explorer.

The project studies BB84 Quantum Key Distribution through protocol-level simulation, Qiskit circuit simulation, Qiskit Aer noisy simulation, IBM Quantum hardware runs, and an interactive Streamlit dashboard. Across the project, the main goal is to understand how BB84-style communication behaves under eavesdropping, channel noise, error correction, privacy amplification, and real-device imperfections.

The v2.0 project pipeline is:

```text
BB84 key generation
→ Eve attack and channel noise modeling
→ QBER calculation
→ parity-based error correction
→ privacy amplification
→ final key derivation
→ message encryption/decryption
```

## Main Findings

### 1. Eve Interception Increases QBER

The intercept-resend attack increases the Quantum Bit Error Rate because Eve does not always measure in the same basis as Alice.

When Eve chooses the wrong basis, her measurement can disturb the transmitted state. This disturbance appears as mismatches between Alice and Bob's sifted keys.

The simulation follows the expected approximate relationship:

```text
QBER ≈ Eve interception probability × 25%
```

This confirms the central BB84 idea that eavesdropping can be detected statistically through measurement disturbance.

### 2. Channel Noise Also Increases QBER

The project also models normal channel noise using a bit-flip probability.

This shows that QBER can increase even when Eve is absent. As channel noise probability increases, Alice and Bob observe more mismatches in their sifted keys.

This result is important because real communication channels are not perfectly clean. A high QBER may indicate eavesdropping, noise, device imperfections, or a combination of these factors.

### 3. QBER Is a Warning Signal, Not a Complete Diagnosis

The Eve-vs-noise comparison experiment compares four scenarios:

1. Clean channel
2. Noise only
3. Eve only
4. Eve + noise

The clean channel produces the lowest QBER. Noise-only and Eve-only scenarios both increase QBER, while the combined Eve-plus-noise scenario usually produces the highest QBER.

This shows that QBER is useful as a warning signal, but QBER alone does not identify the exact cause of errors. It tells Alice and Bob that the channel is disturbed, but not whether the disturbance comes from Eve, natural noise, or both.

### 4. Qiskit Confirms the BB84 Basis Rule

The Qiskit circuit demonstration confirms the basic rule used in the protocol-level simulator:

```text
same basis → Bob recovers Alice's bit
different basis → Bob receives an approximately random result
```

Same-basis circuits produce deterministic measurement behavior in ideal simulation. Different-basis circuits produce approximately random measurement outcomes.

This connects the simplified BB84 protocol model to actual one-qubit quantum circuit behavior.

### 5. Qiskit Aer Adds Circuit-Level Noise

The Qiskit Aer noise model experiment compares ideal BB84 circuits with noisy circuit simulations.

The noisy simulation includes gate noise and readout error. As the noise probability increases, the probability of measuring the wrong bit also increases.

This connects the earlier protocol-level noise model to circuit-level quantum simulation. It shows how errors can arise not only from abstract channel noise, but also from imperfect gates and measurements.

### 6. IBM Quantum Hardware Shows Real-Device Behavior

The IBM Quantum hardware demonstration runs selected BB84 circuits on real quantum hardware.

Same-basis circuits should mostly recover Alice's bit, while different-basis circuits should be closer to random. However, real hardware introduces device-level noise, measurement imperfections, and other deviations from ideal simulation.

This hardware experiment adds a practical layer to the project by showing that real quantum devices do not behave exactly like ideal simulators.

### 7. Error Correction Has a Reliability-Cost Tradeoff

The parity-based error correction experiment studies different block sizes and correction pass counts.

The results show a tradeoff:

```text
more correction passes → higher chance of matching keys
more correction passes → more parity checks required
```

This demonstrates that error correction improves reliability, but it also has a communication and computation cost.

The parameter sweep makes the error correction step more analytical by showing when the correction method works well and when it becomes expensive or insufficient.

### 8. Privacy Amplification Has a Compression-Capacity Tradeoff

The privacy amplification parameter sweep studies different compression ratios and message lengths.

The results show that privacy amplification creates a tradeoff:

```text
stronger compression → shorter final key
weaker compression → more usable key material
```

If the final key is too short for the message, the message exchange fails because there is not enough derived key material. This shows why final key capacity matters after reconciliation and privacy amplification.

### 9. The Full Pipeline Connects Multiple Concepts

The project connects several areas:

- quantum information
- cryptography
- probability
- Python simulation
- Qiskit circuit modeling
- IBM Quantum hardware
- error correction
- privacy amplification
- interactive visualization

The project begins with a basic BB84 simulator and gradually expands into a broader analysis platform for studying quantum-safe communication behavior.

## Conclusion

The Quantum-Safe Communication Explorer demonstrates how BB84-style quantum key distribution can be simulated, tested, and visualized across multiple conditions.

The project shows that:

- Eve's intercept-resend attack increases QBER.
- Channel noise also increases QBER.
- QBER is useful as a warning signal but does not identify the exact cause of errors.
- Qiskit circuits confirm the basis behavior used in the simulator.
- Qiskit Aer noise models connect protocol-level and circuit-level noise.
- IBM Quantum hardware introduces real-device imperfections.
- Error correction improves key agreement but has a cost.
- Privacy amplification compresses reconciled keys but reduces final key capacity.

Together, these results create a complete BB84-inspired communication pipeline from quantum key generation to encrypted message transmission.
