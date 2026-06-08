# Quantum-Safe Communication Explorer

## Abstract

This project explores quantum-safe communication through a simulation of the BB84 Quantum Key Distribution protocol. It models key generation between Alice and Bob, introduces Eve as an intercept-resend attacker, measures the Quantum Bit Error Rate, and demonstrates message encryption using BB84-generated keys. The project also includes a Qiskit-based circuit demonstration to connect the protocol-level simulation to actual quantum circuit behavior.

## 1. Motivation

Modern secure communication relies on cryptographic systems that may be threatened by future large-scale quantum computers. This project investigates how quantum information principles can be used to detect eavesdropping and support secure key generation.

The goal is not to build production cryptographic software, but to create an educational and experimental platform for understanding BB84, QBER, eavesdropping detection, and quantum-safe communication.

## 2. Background

### 2.1 Classical vs Quantum-Safe Communication

Classical public-key systems such as RSA and ECC may become vulnerable to scalable quantum computers. Quantum-safe communication explores methods that remain secure in a quantum future.

### 2.2 BB84 Protocol

BB84 is a quantum key distribution protocol where Alice sends qubits encoded using randomly selected bases. Bob independently chooses measurement bases. After transmission, Alice and Bob publicly compare bases and keep only the bits where their bases matched.

### 2.3 Quantum Bit Error Rate

The Quantum Bit Error Rate measures the fraction of mismatched bits between Alice and Bob’s sifted keys. A high QBER may indicate eavesdropping or excessive noise.

## 3. Simulation Design

The project models:

- Alice’s random bit generation
- Alice’s random basis selection
- Bob’s random basis selection
- Key sifting
- Eve’s intercept-resend attack
- QBER calculation
- Message encryption using BB84-generated keys
- Qiskit-based circuit validation

## 4. Eavesdropping Experiment

Eve intercepts a configurable percentage of qubits. She randomly selects a basis, measures the qubit, and resends her measured result to Bob.

The expected relationship is:

QBER ≈ Eve interception probability × 25%

This happens because Eve chooses the wrong basis about half the time, and when she does, Bob has about a 50% chance of receiving a different bit.

## 5. Results

The simulation shows that QBER increases as Eve intercepts more qubits. This confirms that BB84 can statistically detect eavesdropping through disturbance in the quantum channel.

The Qiskit circuit demonstration also confirms the simplified rule used in the protocol simulator:

- same basis → Bob recovers Alice’s bit
- different basis → Bob receives an approximately random result

## 6. Message Encryption Demo

After BB84 key generation, the project checks whether QBER is below the selected threshold. If the channel appears safe, the generated key is used for XOR-based educational encryption. If the QBER is too high, communication is aborted.

This demonstrates the communication flow:

BB84 key generation → QBER security check → simplified reconciliation → message encryption → message decryption

## 7. Limitations

This project is an educational simulation and not production cryptographic software.

Current limitations:

- No real quantum hardware communication channel
- XOR encryption is used only for demonstration
- Simplified reconciliation removes mismatched positions using simulation-only access
- No production-grade error correction
- No privacy amplification
- No authenticated public channel
- No real-world key management

## 8. Future Work

Possible future improvements include:

- Implementing simplified error correction
- Adding privacy amplification
- Running circuits on IBM Quantum hardware
- Replacing XOR with AES for demonstration
- Adding noise models using Qiskit Aer
- Deploying the Streamlit dashboard publicly
- Writing a blog series explaining each stage

## 9. Conclusion

This project demonstrates how quantum information principles can support secure communication. By simulating BB84, eavesdropping, QBER, message encryption, and Qiskit circuit behavior, the project connects mathematics, computer science, cryptography, and quantum computing in one coherent system.