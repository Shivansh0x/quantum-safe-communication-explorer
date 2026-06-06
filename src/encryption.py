import numpy as np

from bb84 import run_bb84_with_eve

def message_to_bits(message):
    message_bytes = message.encode("utf-8")
    byte_array = np.frombuffer(message_bytes, dtype=np.uint8)
    return np.unpackbits(byte_array)

def bits_to_message(bits):
    bits = np.array(bits, dtype=np.uint8)

    if len(bits) % 8 != 0:
        raise ValueError("Bit array length must be a multiple of 8.")

    byte_array = np.packbits(bits)
    return byte_array.tobytes().decode("utf-8", errors="replace")

def xor_bits(message_bits, key_bits):
    return np.bitwise_xor(message_bits, key_bits)

def encrypt_message_xor(message, key_bits):
    message_bits = message_to_bits(message)

    if len(key_bits) < len(message_bits):
        raise ValueError(
            f"Key too short. Message needs {len(message_bits)} bits, "
            f"but key has only {len(key_bits)} bits. "
            "Increase the number of BB84 qubits."
        )
    
    key_used=np.array(key_bits[:len(message_bits)], dtype=np.uint8)
    ciphertext_bits = xor_bits(message_bits, key_used)

    return ciphertext_bits, key_used

def decrypt_message_xor(ciphertext_bits, key_bits):
    ciphertext_bits = np.array(ciphertext_bits, dtype=np.uint8)

    if len(key_bits) < len(ciphertext_bits):
        raise ValueError(
            f"Key too short. Ciphertext needs {len(ciphertext_bits)} bits, "
            f"but key has only {len(key_bits)} bits."
        )
    
    key_used = np.array(key_bits[:len(ciphertext_bits)], dtype=np.uint8)
    decrypted_bits = xor_bits(ciphertext_bits, key_used)

    return bits_to_message(decrypted_bits)

def bits_to_display_string(bits, max_length=128):
    bit_string = "".join(str(int(bit)) for bit in bits)

    if len(bit_string) > max_length:
        return bit_string[:max_length] + "..."
    
    return bit_string

def reconcile_keys_for_simulation(alice_key: np.ndarray, bob_key: np.ndarray):
    """
    Simplified educational key reconciliation.

    In real BB84, Alice and Bob would use an authenticated public discussion
    protocol for error correction, followed by privacy amplification.

    In this simulation, we directly remove mismatched positions so that the
    remaining keys match. This is only for educational demonstration and is
    not a production cryptographic protocol.
    """
    matching_positions = alice_key == bob_key

    reconciled_alice_key = alice_key[matching_positions]
    reconciled_bob_key = bob_key[matching_positions]

    mismatched_bits_removed = int(np.sum(~matching_positions))

    return reconciled_alice_key, reconciled_bob_key, mismatched_bits_removed

def run_secure_message_exchange(
    message: str,
    n_qubits: int = 5000,
    eve_intercept_prob: float = 0.0,
    qber_threshold: float = 0.11,
    use_simplified_reconciliation: bool = True
) -> dict:
    """
    Run a simplified secure communication demo.

    1. Use BB84 to generate Alice and Bob's sifted keys.
    2. Calculate QBER.
    3. Abort if QBER is above the threshold.
    4. If enabled, apply simplified educational reconciliation.
    5. Encrypt and decrypt the message using the final matching key.

    Note:
    This is an educational simulation, not production cryptography.
    """

    bb84_result = run_bb84_with_eve(
        n=n_qubits,
        eve_intercept_prob=eve_intercept_prob
    )

    raw_alice_key = np.array(bb84_result["alice_key"], dtype=np.uint8)
    raw_bob_key = np.array(bb84_result["bob_key"], dtype=np.uint8)
    qber = bb84_result["qber"]

    message_bits = message_to_bits(message)

    raw_mismatches = int(np.sum(raw_alice_key != raw_bob_key))

    if qber > qber_threshold:
        return {
            "status": "aborted",
            "reason": "QBER exceeded threshold. Possible eavesdropping detected.",
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "raw_alice_key_length": len(raw_alice_key),
            "raw_bob_key_length": len(raw_bob_key),
            "alice_key_length": len(raw_alice_key),
            "bob_key_length": len(raw_bob_key),
            "raw_mismatches": raw_mismatches,
            "mismatched_bits_removed": 0,
            "reconciliation_used": False,
            "ciphertext_bits": None,
            "ciphertext_display": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    if use_simplified_reconciliation:
        alice_key, bob_key, mismatched_bits_removed = reconcile_keys_for_simulation(
            raw_alice_key,
            raw_bob_key
        )
        reconciliation_used = True
    else:
        alice_key = raw_alice_key
        bob_key = raw_bob_key
        mismatched_bits_removed = 0
        reconciliation_used = False

    if not np.array_equal(alice_key, bob_key):
        return {
            "status": "aborted",
            "reason": (
                "Alice and Bob's keys do not match exactly. "
                "Enable simplified reconciliation or implement error correction."
            ),
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "raw_alice_key_length": len(raw_alice_key),
            "raw_bob_key_length": len(raw_bob_key),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "raw_mismatches": raw_mismatches,
            "mismatched_bits_removed": mismatched_bits_removed,
            "reconciliation_used": reconciliation_used,
            "ciphertext_bits": None,
            "ciphertext_display": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    if len(alice_key) < len(message_bits) or len(bob_key) < len(message_bits):
        return {
            "status": "aborted",
            "reason": "Final key is too short for this message. Increase n_qubits.",
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "raw_alice_key_length": len(raw_alice_key),
            "raw_bob_key_length": len(raw_bob_key),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "raw_mismatches": raw_mismatches,
            "mismatched_bits_removed": mismatched_bits_removed,
            "reconciliation_used": reconciliation_used,
            "ciphertext_bits": None,
            "ciphertext_display": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    ciphertext_bits, key_used_by_alice = encrypt_message_xor(message, alice_key)
    decrypted_message = decrypt_message_xor(ciphertext_bits, bob_key)

    return {
        "status": "success",
        "reason": "Message encrypted and decrypted successfully.",
        "qber": qber,
        "qber_threshold": qber_threshold,
        "eve_intercept_prob": eve_intercept_prob,
        "message": message,
        "message_bits_required": len(message_bits),
        "raw_alice_key_length": len(raw_alice_key),
        "raw_bob_key_length": len(raw_bob_key),
        "alice_key_length": len(alice_key),
        "bob_key_length": len(bob_key),
        "raw_mismatches": raw_mismatches,
        "mismatched_bits_removed": mismatched_bits_removed,
        "reconciliation_used": reconciliation_used,
        "key_used": key_used_by_alice,
        "ciphertext_bits": ciphertext_bits,
        "ciphertext_display": bits_to_display_string(ciphertext_bits),
        "decrypted_message": decrypted_message,
        "bb84_result": bb84_result
    }