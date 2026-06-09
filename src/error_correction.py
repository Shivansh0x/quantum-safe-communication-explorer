import numpy as np


def calculate_parity(bits):
    """
    Return parity of a bit array.
    0 means even number of 1s.
    1 means odd number of 1s.
    """
    return int(np.sum(bits) % 2)


def find_error_index_by_parity(alice_key, bob_key, indices):
    """
    Locate one likely error inside a block using binary parity checks.

    This assumes the block has an odd number of mismatches.
    """
    indices = np.array(indices)

    parity_checks = 0

    while len(indices) > 1:
        mid = len(indices) // 2
        left = indices[:mid]
        right = indices[mid:]

        parity_checks += 1

        if calculate_parity(alice_key[left]) != calculate_parity(bob_key[left]):
            indices = left
        else:
            indices = right

    return int(indices[0]), parity_checks


def parity_error_correction(alice_key, bob_key, block_size=15, passes=5, seed=42):
    """
    Perform simplified parity-based error correction.

    Method:
    - Split the key into blocks.
    - Compare Alice and Bob's parity for each block.
    - If block parity differs, locate one likely error using binary parity checks.
    - Flip Bob's bit at the detected position.
    - Repeat over multiple shuffled passes.

    Returns corrected keys and diagnostic information.
    """
    alice = np.array(alice_key, dtype=np.uint8).copy()
    bob = np.array(bob_key, dtype=np.uint8).copy()

    if len(alice) != len(bob):
        raise ValueError("Alice and Bob keys must have the same length.")

    rng = np.random.default_rng(seed)

    n = len(alice)
    raw_mismatches = int(np.sum(alice != bob))

    corrections_applied = 0
    parity_checks = 0
    corrected_indices = []

    for pass_number in range(passes):
        indices = np.arange(n)

        if pass_number > 0:
            rng.shuffle(indices)

        for start in range(0, n, block_size):
            block_indices = indices[start:start + block_size]

            if len(block_indices) == 0:
                continue

            parity_checks += 1

            alice_parity = calculate_parity(alice[block_indices])
            bob_parity = calculate_parity(bob[block_indices])

            if alice_parity != bob_parity:
                error_index, checks_used = find_error_index_by_parity(
                    alice,
                    bob,
                    block_indices
                )

                parity_checks += checks_used

                bob[error_index] = 1 - bob[error_index]
                corrections_applied += 1
                corrected_indices.append(error_index)

    final_mismatches = int(np.sum(alice != bob))

    return {
        "corrected_alice_key": alice,
        "corrected_bob_key": bob,
        "raw_mismatches": raw_mismatches,
        "final_mismatches": final_mismatches,
        "corrections_applied": corrections_applied,
        "parity_checks": parity_checks,
        "corrected_indices": corrected_indices,
        "block_size": block_size,
        "passes": passes,
        "success": final_mismatches == 0
    }