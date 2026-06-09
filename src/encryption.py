import numpy as np

from bb84 import run_bb84_with_eve
from error_correction import parity_error_correction
from privacy_amplification import derive_final_key_bits, key_fingerprint

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

def run_secure_message_exchange(message, n_qubits = 5000, eve_intercept_prob = 0.0, qber_threshold = 0.11,
    use_error_correction = True, error_correction_block_size = 16, error_correction_passes = 5, use_privacy_amplification = True,
    privacy_compression_ratio= 0.5):
    """
    Run the secure communication demo.

    Pipeline:
    1. Generate BB84 sifted keys.
    2. Check QBER.
    3. Apply parity-based error correction.
    4. Apply privacy amplification / final key derivation.
    5. Encrypt and decrypt the message.
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
            "reconciled_key_length": 0,
            "alice_key_length": len(raw_alice_key),
            "bob_key_length": len(raw_bob_key),
            "raw_mismatches": raw_mismatches,
            "final_mismatches": raw_mismatches,
            "corrections_applied": 0,
            "parity_checks": 0,
            "error_correction_used": False,
            "privacy_amplification_used": False,
            "privacy_compression_ratio": privacy_compression_ratio,
            "final_key_fingerprint": None,
            "ciphertext_bits": None,
            "ciphertext_display": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    if use_error_correction:
        correction_result = parity_error_correction(
            raw_alice_key,
            raw_bob_key,
            block_size=error_correction_block_size,
            passes=error_correction_passes
        )

        reconciled_alice_key = correction_result["corrected_alice_key"]
        reconciled_bob_key = correction_result["corrected_bob_key"]
        final_mismatches = correction_result["final_mismatches"]
        corrections_applied = correction_result["corrections_applied"]
        parity_checks = correction_result["parity_checks"]
        error_correction_used = True

    else:
        reconciled_alice_key = raw_alice_key
        reconciled_bob_key = raw_bob_key
        final_mismatches = raw_mismatches
        corrections_applied = 0
        parity_checks = 0
        error_correction_used = False

    if final_mismatches != 0:
        return {
            "status": "aborted",
            "reason": (
                "Alice and Bob's keys still do not match after correction. "
                "Try increasing qubits, reducing Eve probability, or increasing correction passes."
            ),
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "raw_alice_key_length": len(raw_alice_key),
            "raw_bob_key_length": len(raw_bob_key),
            "reconciled_key_length": len(reconciled_alice_key),
            "alice_key_length": len(reconciled_alice_key),
            "bob_key_length": len(reconciled_bob_key),
            "raw_mismatches": raw_mismatches,
            "final_mismatches": final_mismatches,
            "corrections_applied": corrections_applied,
            "parity_checks": parity_checks,
            "error_correction_used": error_correction_used,
            "privacy_amplification_used": False,
            "privacy_compression_ratio": privacy_compression_ratio,
            "final_key_fingerprint": None,
            "ciphertext_bits": None,
            "ciphertext_display": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    if use_privacy_amplification:
        max_final_key_bits = int(len(reconciled_alice_key) * privacy_compression_ratio)

        if len(message_bits) > max_final_key_bits:
            return {
                "status": "aborted",
                "reason": (
                    "Not enough reconciled key material after privacy amplification. "
                    "Increase n_qubits or shorten the message."
                ),
                "qber": qber,
                "qber_threshold": qber_threshold,
                "eve_intercept_prob": eve_intercept_prob,
                "message": message,
                "message_bits_required": len(message_bits),
                "raw_alice_key_length": len(raw_alice_key),
                "raw_bob_key_length": len(raw_bob_key),
                "reconciled_key_length": len(reconciled_alice_key),
                "alice_key_length": max_final_key_bits,
                "bob_key_length": max_final_key_bits,
                "raw_mismatches": raw_mismatches,
                "final_mismatches": final_mismatches,
                "corrections_applied": corrections_applied,
                "parity_checks": parity_checks,
                "error_correction_used": error_correction_used,
                "privacy_amplification_used": True,
                "privacy_compression_ratio": privacy_compression_ratio,
                "final_key_fingerprint": None,
                "ciphertext_bits": None,
                "ciphertext_display": None,
                "decrypted_message": None,
                "bb84_result": bb84_result
            }

        alice_key = derive_final_key_bits(
            reconciled_alice_key,
            output_length_bits=len(message_bits)
        )

        bob_key = derive_final_key_bits(
            reconciled_bob_key,
            output_length_bits=len(message_bits)
        )

        privacy_amplification_used = True

    else:
        alice_key = reconciled_alice_key
        bob_key = reconciled_bob_key
        privacy_amplification_used = False

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
                "reconciled_key_length": len(reconciled_alice_key),
                "alice_key_length": len(alice_key),
                "bob_key_length": len(bob_key),
                "raw_mismatches": raw_mismatches,
                "final_mismatches": final_mismatches,
                "corrections_applied": corrections_applied,
                "parity_checks": parity_checks,
                "error_correction_used": error_correction_used,
                "privacy_amplification_used": privacy_amplification_used,
                "privacy_compression_ratio": privacy_compression_ratio,
                "final_key_fingerprint": None,
                "ciphertext_bits": None,
                "ciphertext_display": None,
                "decrypted_message": None,
                "bb84_result": bb84_result
            }

    if not np.array_equal(alice_key, bob_key):
        return {
            "status": "aborted",
            "reason": "Final derived keys do not match.",
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "raw_alice_key_length": len(raw_alice_key),
            "raw_bob_key_length": len(raw_bob_key),
            "reconciled_key_length": len(reconciled_alice_key),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "raw_mismatches": raw_mismatches,
            "final_mismatches": final_mismatches,
            "corrections_applied": corrections_applied,
            "parity_checks": parity_checks,
            "error_correction_used": error_correction_used,
            "privacy_amplification_used": privacy_amplification_used,
            "privacy_compression_ratio": privacy_compression_ratio,
            "final_key_fingerprint": None,
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
        "reconciled_key_length": len(reconciled_alice_key),
        "alice_key_length": len(alice_key),
        "bob_key_length": len(bob_key),
        "raw_mismatches": raw_mismatches,
        "final_mismatches": final_mismatches,
        "corrections_applied": corrections_applied,
        "parity_checks": parity_checks,
        "error_correction_used": error_correction_used,
        "privacy_amplification_used": privacy_amplification_used,
        "privacy_compression_ratio": privacy_compression_ratio,
        "final_key_fingerprint": key_fingerprint(alice_key),
        "key_used": key_used_by_alice,
        "ciphertext_bits": ciphertext_bits,
        "ciphertext_display": bits_to_display_string(ciphertext_bits),
        "decrypted_message": decrypted_message,
        "bb84_result": bb84_result
    }