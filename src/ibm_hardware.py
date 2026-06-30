import pandas as pd

from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from qiskit_bb84 import create_bb84_circuit


def get_ibm_service():
    """
    Load the saved IBM Quantum account.

    The account should be saved locally using:
    QiskitRuntimeService.save_account(...)
    """
    return QiskitRuntimeService()


def get_backend(service=None, backend_name: str = None, min_num_qubits: int = 1):
    """
    Select an IBM Quantum backend.

    If backend_name is provided, that backend is used.
    Otherwise, the least busy available backend is selected.
    """
    if service is None:
        service = get_ibm_service()

    if backend_name is not None:
        return service.backend(backend_name)

    return service.least_busy(min_num_qubits=min_num_qubits, operational=True)


def prepare_circuit_for_backend(circuit, backend, optimization_level: int = 1):
    """
    Transpile a circuit for a selected IBM Quantum backend.
    """
    pass_manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=optimization_level
    )

    return pass_manager.run(circuit)


def extract_sampler_counts(pub_result, circuit):
    """
    Extract counts from a Sampler V2 result.

    Sampler V2 stores measurement results under the circuit's classical
    register name. This helper reads the first classical register.
    """
    if len(circuit.cregs) == 0:
        raise ValueError("Circuit has no classical registers.")

    classical_register_name = circuit.cregs[0].name
    register_data = getattr(pub_result.data, classical_register_name)

    return register_data.get_counts()


def run_single_bb84_on_ibm_hardware(
    alice_bit: int,
    alice_basis: str,
    bob_basis: str,
    backend_name: str = None,
    shots: int = 1000,
    optimization_level: int = 1
) -> dict:
    """
    Run a single BB84 circuit case on IBM Quantum hardware.
    """
    service = get_ibm_service()
    backend = get_backend(
        service=service,
        backend_name=backend_name,
        min_num_qubits=1
    )

    circuit = create_bb84_circuit(
        alice_bit=alice_bit,
        alice_basis=alice_basis,
        bob_basis=bob_basis
    )

    isa_circuit = prepare_circuit_for_backend(
        circuit=circuit,
        backend=backend,
        optimization_level=optimization_level
    )

    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)

    print("Submitted IBM Quantum job:", job.job_id())
    print("Backend:", backend.name)

    result = job.result()
    pub_result = result[0]

    counts = extract_sampler_counts(pub_result, isa_circuit)

    return {
        "alice_bit": alice_bit,
        "alice_basis": alice_basis,
        "bob_basis": bob_basis,
        "same_basis": alice_basis == bob_basis,
        "backend_name": backend.name,
        "job_id": job.job_id(),
        "shots": shots,
        "counts": counts
    }


def counts_to_probabilities(counts: dict, shots: int) -> dict:
    """
    Convert counts into probabilities for 0 and 1.
    """
    return {
        "prob_0": counts.get("0", 0) / shots,
        "prob_1": counts.get("1", 0) / shots
    }


def run_bb84_hardware_case_set(
    backend_name: str = None,
    shots: int = 1000,
    optimization_level: int = 1
) -> pd.DataFrame:
    """
    Run a small set of BB84 cases on IBM Quantum hardware.

    This keeps the hardware experiment small:
    - same-basis Z case
    - same-basis X case
    - different-basis Z-to-X case
    - different-basis X-to-Z case
    """
    cases = [
        {
            "case": "same_basis_Z_bit_0",
            "alice_bit": 0,
            "alice_basis": "Z",
            "bob_basis": "Z"
        },
        {
            "case": "same_basis_X_bit_0",
            "alice_bit": 0,
            "alice_basis": "X",
            "bob_basis": "X"
        },
        {
            "case": "different_basis_Z_to_X",
            "alice_bit": 0,
            "alice_basis": "Z",
            "bob_basis": "X"
        },
        {
            "case": "different_basis_X_to_Z",
            "alice_bit": 0,
            "alice_basis": "X",
            "bob_basis": "Z"
        }
    ]

    rows = []

    for case in cases:
        result = run_single_bb84_on_ibm_hardware(
            alice_bit=case["alice_bit"],
            alice_basis=case["alice_basis"],
            bob_basis=case["bob_basis"],
            backend_name=backend_name,
            shots=shots,
            optimization_level=optimization_level
        )

        probabilities = counts_to_probabilities(
            result["counts"],
            shots=shots
        )

        rows.append({
            "case": case["case"],
            "alice_bit": result["alice_bit"],
            "alice_basis": result["alice_basis"],
            "bob_basis": result["bob_basis"],
            "same_basis": result["same_basis"],
            "backend_name": result["backend_name"],
            "job_id": result["job_id"],
            "shots": result["shots"],
            "count_0": result["counts"].get("0", 0),
            "count_1": result["counts"].get("1", 0),
            "prob_0": probabilities["prob_0"],
            "prob_1": probabilities["prob_1"]
        })

    return pd.DataFrame(rows)