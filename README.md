# Quantum Safe Communication Explorer

## Version 0.1: BB84 Without Eavesdropping

This project simulates the BB84 Quantum Key Distribution protocol to explore quantum-safe communication.

The first vesrsion simulates BB84 without eavesdropping. Alice generates random bits and bases, Bob generates random bases and both of them only keep positions where their bases match. This allowes them to produce a shared key.

## Features

- Random bit generation
- Random basis generation using Z and X bases
- Bob measurement simulation
- Key sifting
- QBER calculation
- BB84 simulation without Eve

## Initial Observation:
When there is no eavesdropper, Alice and Bob generate matching sifted keys and the QBER is 0. 

## Next Step 
The next version will introduce Eve using an intercept-resend attack and measure how eavesdropping increases the Quantum Bit Error Rate. 