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

def run_secure_message_exchange(message, n_qubits=5000, eve_intercept_prob=0.0, qber_threshold=0.11):
    """
    Run a simplified secure communication demo.

    1. Use BB84 to generate Alice and Bob's sifted keys.
    2. Calculate QBER.
    3. Abort if QBER is above the threshold.
    4. Abort if Alice and Bob's keys do not exactly match.
       This simplified v0.4 implementation does not include error correction.
    5. If the keys match, encrypt and decrypt the message using XOR.

    Note:
    This is an educational simulation, not production cryptography.
    """
    bb84_result = run_bb84_with_eve(n=n_qubits, eve_intercept_prob=eve_intercept_prob)

    alice_key = np.array(bb84_result["alice_key"], dtype=np.uint8)
    bob_key = np.array(bb84_result["bob_key"], dtype=np.uint8)
    qber = bb84_result["qber"]

    message_bits = message_to_bits(message)

    if qber > qber_threshold:
        return {
            "status": "aborted",
            "reason": "QBER exceeded threshold. Possible eavesdropping detected.",
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "ciphertext_bits": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }

    if len(alice_key) < len(message_bits) or len(bob_key) < len(message_bits):
        return {
            "status": "aborted",
            "reason": "Generated key is too short for this message. Increase n_qubits.",
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "ciphertext_bits": None,
            "decrypted_message": None,
            "bb84_result": bb84_result
        }
    
    if not np.array_equal(alice_key[:len(message_bits)], bob_key[:len(message_bits)]):
        return {
            "status": "aborted",
            "reason": (
                "Alice and Bob's keys do not match exactly. "
                "Error correction is needed before encryption."
            ),
            "qber": qber,
            "qber_threshold": qber_threshold,
            "eve_intercept_prob": eve_intercept_prob,
            "message": message,
            "message_bits_required": len(message_bits),
            "alice_key_length": len(alice_key),
            "bob_key_length": len(bob_key),
            "ciphertext_bits": None,
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
        "alice_key_length": len(alice_key),
        "bob_key_length": len(bob_key),
        "key_used": key_used_by_alice,
        "ciphertext_bits": ciphertext_bits,
        "ciphertext_display": bits_to_display_string(ciphertext_bits),
        "decrypted_message": decrypted_message,
        "bb84_result": bb84_result
    }