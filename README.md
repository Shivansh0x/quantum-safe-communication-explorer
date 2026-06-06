# Quantum Safe Communication Explorer

## Version History

- v0.1: Implemented BB84 without eavesdropping
- v0.2: Added Eve intercept-resend attack simulation
- v0.3: Added QBER experiment and visualization
- v0.3.1: Fixed typo in QBER graph label

## Version 0.1: BB84 Without Eavesdropping

This project simulates the BB84 Quantum Key Distribution protocol to explore quantum-safe communication.

The first vesrsion simulates BB84 without eavesdropping. Alice generates random bits and bases, Bob generates random bases and both of them only keep positions where their bases match. This allowes them to produce a shared key.

### Features

- Random bit generation
- Random basis generation using Z and X bases
- Bob measurement simulation
- Key sifting
- QBER calculation
- BB84 simulation without Eve

### Initial Observation:
When there is no eavesdropper, Alice and Bob generate matching sifted keys and the QBER is 0. 

### Next Step 
The next version will introduce Eve using an intercept-resend attack and measure how eavesdropping increases the Quantum Bit Error Rate. 

## Version 0.2: Eve Intercept-Resend Attack Simulation

This version adds an eavesdropping model to the BB84 simulation. 

In BB84, Alice sends qubits using randomly chosen bases, while Bob independently chooses his own measurement bases. In this version, an eavesdropper named Eve can intercept a percentage of the transmitted qubits. Even randomly chooses a basis, measures the qubit, and resends her measured result to Bob. 

Because Eve does not always choose the correct basis, her measurement can disturb the transmitted state. This disturbance appears as errors in Alice and Bob’s sifted keys.

### New Features
- Added Eve as an intercept-resend attacker
- Added configurable Eve interception probability
- Simulated Eve’s random basis choices
- Simulated Bob’s measurement after Eve resends qubits
- Calculated QBER after eavesdropping
- Tested the protocol with different interception probabilities

### Key Observation
When Eve intercepts qubits, the Quantum Bit Error Rate increases. For an intercept-resend attack, the expected QBER is approximately:

```text
QBER ≈ Eve interception probability x 25%
```

For example, if Eve intercepts 25% of the qubits, the expected QBER is roughly:

```text
0.25 x 0.25 = 0.0625
```

or about 6.25%

### Next Step

The next version will run the simulation across multiple Eve interception probabilities and generate a graph showing how QBER changes as Eve's attack strength increases. 

## Version 0.3: QBER Experiment and Visualization

This version extends the Eve intercept-resend simulation by running BB84 across multiple Eve interception probabilities and measuring how the Quantum Bit Error Rate changes.

Instead of testing only one attack level, the experiment now evaluates Eve interception rates from 0% to 100%. For each interception rate, the simulation is repeated multiple times, and the average QBER is calculated.

### New Features

* Added repeated QBER experiments across multiple Eve interception rates
* Added average QBER calculation
* Added QBER standard deviation calculation
* Added expected QBER comparison
* Saved experiment results as a CSV file
* Generated a QBER vs Eve interception probability graph

### Key Result

The simulation confirms the expected BB84 behavior:

```text
QBER ≈ Eve interception probability × 25%
```

As Eve intercepts more qubits, the QBER increases. This demonstrates how BB84 can statistically detect eavesdropping through disturbance in the quantum channel.

### Output Files

```text
results/qber_experiment_results.csv
figures/qber_vs_eve_interception.png
```

### Next Step

The next version will use the sifted BB84 key to encrypt and decrypt a message, connecting quantum key distribution to practical secure communication.

## Version 0.4: Message Encryption Using the BB84 Key

This version connects the BB84 key generation simulation to a simple secure communication demo.

After Alice and Bob generate sifted keys through BB84, the system checks the Quantum Bit Error Rate. If the QBER is above the safety threshold, communication is aborted because possible eavesdropping has been detected. If the QBER is acceptable and Alice and Bob's keys match, the generated key is used to encrypt and decrypt a message.

### New Features

- Added message-to-bits conversion
- Added bits-to-message conversion
- Added XOR-based educational encryption
- Added decryption using Bob's BB84-generated key
- Added QBER threshold decision logic
- Added automatic communication abort if QBER is too high
- Added automatic abort if the generated key is too short
- Added automatic abort if Alice and Bob's keys do not match exactly
- Added message encryption notebook

### Security Note

This version uses XOR encryption as an educational one-time-pad style demonstration. It is not production cryptography.

This version also does not implement BB84 error correction or privacy amplification. If Alice and Bob's generated keys do not match exactly, communication is aborted. A future version may add simplified error reconciliation and privacy amplification.

### Key Result

The project now demonstrates the full basic flow of quantum-safe communication:

```text
BB84 key generation
→ QBER security check
→ message encryption
→ message decryption
→ abort if attack/noise is detected
```