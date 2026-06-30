import numpy as np
import pandas as pd

from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

from qiskit_bb84 import create_bb84_circuit


def create_simple_noise_model(
    single_qubit_gate_error: float = 0.01,
    readout_error: float = 0.01
) -> NoiseModel:
    """
    Create a simple Qiskit Aer noise model.

    The model includes:
    - depolarizing noise on one-qubit gates
    - readout error during measurement
    """

    if single_qubit_gate_error < 0 or single_qubit_gate_error > 1:
        raise ValueError("single_qubit_gate_error must be between 0 and 1.")

    if readout_error < 0 or readout_error > 1:
        raise ValueError("readout_error must be between 0 and 1.")

    noise_model = NoiseModel()

    if single_qubit_gate_error > 0:
        gate_error = depolarizing_error(single_qubit_gate_error, 1)

        noise_model.add_all_qubit_quantum_error(
            gate_error,
            ["x", "h"]
        )

    if readout_error > 0:
        readout_error_model = ReadoutError([
            [1 - readout_error, readout_error],
            [readout_error, 1 - readout_error]
        ])

        noise_model.add_all_qubit_readout_error(readout_error_model)

    return noise_model


def run_circuit_counts(circuit, shots: int = 1000, noise_model: NoiseModel = None):
    """
    Run a circuit using Qiskit Aer and return measurement counts.
    """

    simulator = AerSimulator(noise_model=noise_model)
    compiled_circuit = transpile(circuit, simulator)

    job = simulator.run(compiled_circuit, shots=shots)
    result = job.result()

    return result.get_counts(compiled_circuit)


def calculate_probability_of_one(counts: dict, shots: int) -> float:
    """
    Calculate probability of measuring 1.
    """
    return counts.get("1", 0) / shots


def calculate_error_probability(
    counts: dict,
    expected_bit: int,
    shots: int
) -> float:
    """
    Calculate probability of measuring the wrong bit.
    """

    wrong_bit = "1" if expected_bit == 0 else "0"
    return counts.get(wrong_bit, 0) / shots


def compare_ideal_and_noisy_bb84_case(
    alice_bit: int,
    alice_basis: str,
    bob_basis: str,
    single_qubit_gate_error: float = 0.01,
    readout_error: float = 0.01,
    shots: int = 1000
) -> dict:
    """
    Compare one BB84 circuit case under ideal and noisy simulation.
    """

    circuit = create_bb84_circuit(
        alice_bit=alice_bit,
        alice_basis=alice_basis,
        bob_basis=bob_basis
    )

    ideal_counts = run_circuit_counts(
        circuit=circuit,
        shots=shots,
        noise_model=None
    )

    noise_model = create_simple_noise_model(
        single_qubit_gate_error=single_qubit_gate_error,
        readout_error=readout_error
    )

    noisy_counts = run_circuit_counts(
        circuit=circuit,
        shots=shots,
        noise_model=noise_model
    )

    same_basis = alice_basis == bob_basis

    if same_basis:
        expected_bit = alice_bit
        ideal_error_probability = calculate_error_probability(
            ideal_counts,
            expected_bit=expected_bit,
            shots=shots
        )
        noisy_error_probability = calculate_error_probability(
            noisy_counts,
            expected_bit=expected_bit,
            shots=shots
        )
    else:
        expected_bit = None
        ideal_error_probability = None
        noisy_error_probability = None

    return {
        "alice_bit": alice_bit,
        "alice_basis": alice_basis,
        "bob_basis": bob_basis,
        "same_basis": same_basis,
        "shots": shots,
        "single_qubit_gate_error": single_qubit_gate_error,
        "readout_error": readout_error,
        "ideal_counts": ideal_counts,
        "noisy_counts": noisy_counts,
        "ideal_prob_1": calculate_probability_of_one(ideal_counts, shots),
        "noisy_prob_1": calculate_probability_of_one(noisy_counts, shots),
        "ideal_error_probability": ideal_error_probability,
        "noisy_error_probability": noisy_error_probability
    }


def run_qiskit_noise_sweep(
    noise_probabilities=None,
    shots: int = 2000,
    alice_bit: int = 0,
    alice_basis: str = "X",
    bob_basis: str = "X"
) -> pd.DataFrame:
    """
    Run a Qiskit Aer noise sweep for a same-basis BB84 case.

    The default case is:
    Alice bit = 0
    Alice basis = X
    Bob basis = X

    In the ideal circuit, Bob should measure 0.
    As noise increases, the probability of measuring the wrong bit increases.
    """

    if noise_probabilities is None:
        noise_probabilities = np.linspace(0, 0.20, 11)

    rows = []

    for noise_probability in noise_probabilities:
        result = compare_ideal_and_noisy_bb84_case(
            alice_bit=alice_bit,
            alice_basis=alice_basis,
            bob_basis=bob_basis,
            single_qubit_gate_error=float(noise_probability),
            readout_error=float(noise_probability),
            shots=shots
        )

        rows.append({
            "noise_probability": float(noise_probability),
            "alice_bit": alice_bit,
            "alice_basis": alice_basis,
            "bob_basis": bob_basis,
            "shots": shots,
            "ideal_prob_1": result["ideal_prob_1"],
            "noisy_prob_1": result["noisy_prob_1"],
            "ideal_error_probability": result["ideal_error_probability"],
            "noisy_error_probability": result["noisy_error_probability"]
        })

    return pd.DataFrame(rows)