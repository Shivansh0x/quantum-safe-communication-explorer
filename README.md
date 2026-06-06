# Quantum Safe Communication Explorer

## Version 0.2: Eve Intercept-Resend Attack Simulation

This version adds an eavesdropping model to the BB84 simulation. 

In BB84, Alice sends qubits using randomly chosen bases, while Bob independently chooses his own measurement bases. In this version, an eavesdropper named Eve can intercept a percentage of the transmitted qubits. Even randomly chooses a basis, measures the qubit, and resends her measured result to Bob. 

Because Eve does not always choose the correct basis, her measurement can disturb the transmitted state. This disturbance appears as errors in Alice and Bob’s sifted keys.

## New Features
- Added Eve as an intercept-resend attacker
- Added configurable Eve interception probability
- Simulated Eve’s random basis choices
- Simulated Bob’s measurement after Eve resends qubits
- Calculated QBER after eavesdropping
- Tested the protocol with different interception probabilities

## Key Observation
When Eve intercepts qubits, the Quantum Bit Error Rate increases. For an intercept-resend attack, the expected QBER is approximately:

QBER ≈ Eve interception probability x 25%

For example, if Eve intercepts 25% of the qubits, the expected QBER is roughly:

0.25 x 0.25 = 0.0625

or about 6.25%

## Next Step

The next version will run the simulation across multiple Eve interception probabilities and generate a graph showing how QBER changes as Eve's attack strength increases. 