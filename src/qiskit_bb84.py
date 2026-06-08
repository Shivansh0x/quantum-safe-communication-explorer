from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def create_bb84_circuit(alice_bit, alice_basis, bob_basis):
    """
    Create a one-qubit BB84 circuit.

    Alice prepares one of four states:
    - bit 0, Z basis -> |0>
    - bit 1, Z basis -> |1>
    - bit 0, X basis -> |+>
    - bit 1, X basis -> |->

    Bob measures in either the Z or X basis.
    """

    if alice_basis not in ["Z", "X"]:
        raise ValueError("alice_basis must be 'Z' or 'X'.")

    if bob_basis not in ["Z", "X"]:
        raise ValueError("bob_basis must be 'Z' or 'X'.")

    if alice_bit not in [0, 1]:
        raise ValueError("alice_bit must be 0 or 1.")
    
    qc = QuantumCircuit(1, 1)

    if alice_bit==1:
        qc.x(0)
    
    if alice_basis=="X":
        qc.h(0)
    
    qc.barrier()

    if bob_basis=="X":
        qc.h(0)

    qc.measure(0, 0)

    return qc

def run_single_bb84_circuit(alice_bit, alice_basis, bob_basis, shots=1000):
    circuit = create_bb84_circuit(alice_basis=alice_basis, alice_bit=alice_bit, bob_basis=bob_basis)

    simulator = AerSimulator()
    job = simulator.run(circuit, shots=shots)
    result = job.result()
    counts = result.get_counts(circuit)

    return {
        "alice_bit": alice_bit,
        "alice_basis": alice_basis,
        "bob_basis": bob_basis,
        "shots": shots,
        "counts": counts,
        "circuit": circuit
    }

def run_all_bb84_basis_cases(shots=1000):
    results=[]

    for alice_bit in [0,1]:
        for alice_basis in ["Z", "X"]:
            for bob_basis in ["Z", "X"]:
                result = run_single_bb84_circuit(alice_basis=alice_basis, alice_bit=alice_bit, bob_basis=bob_basis, shots=shots)
                results.append(result)
    return results