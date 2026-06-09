import hashlib
import numpy as np

def bits_to_bytes(bits):
    bits = np.array(bits, dtype=np.uint8)

    if len(bits) == 0:
        return b""
    
    padding_needed = (-len(bits)) % 8

    if padding_needed > 0:
        bits = np.concatenate([bits, np.zeros(padding_needed, dtype=np.uint8)])
    
    packed = np.packbits(bits)
    return packed.tobytes()

def bytes_to_bits(data):
    byte_array = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(byte_array)

def derive_final_key_bits(shared_key_bits, output_length_bits, salt=b"QSCE-v1.0"):
    """
    Derive a final key from reconciled BB84 key bits using SHAKE-256.

    The output length should be smaller than the reconciled key length
    when this is used as privacy amplification.
    """
    shared_key_bits = np.array(shared_key_bits, dtype=np.uint8)

    if output_length_bits <= 0:
        raise ValueError("output_length_bits must be positive.")
    
    if len(shared_key_bits) == 0:
        raise ValueError("shared_key_bits cannot be empty.")
    
    input_bytes = bits_to_bytes(shared_key_bits)

    hasher = hashlib.shake_256()
    hasher.update(salt)
    hasher.update(input_bytes)

    output_length_bytes = (output_length_bits + 7)//8
    derived_bytes = hasher.digest(output_length_bytes)

    derived_bits = bytes_to_bits(derived_bytes)

    return derived_bits[:output_length_bits]

def key_fingerprint(key_bits, length=16):
    """
    Create a short fingerprint for display/debugging.
    This should not be treated as a secret key display.
    """
    key_bytes = bits_to_bytes(key_bits)
    digest = hashlib.sha256(key_bytes).hexdigest()
    return digest[:length]