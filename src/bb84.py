import numpy as np

def generate_random_bits(n):
    return np.random.randint(0, 2, size=n)

def generate_random_bases(n):
    return np.random.choice(["Z", "X"], size=n)

def bob_measurement(alice_bits, alice_bases, bob_bases):
    bob_bits = alice_bits.copy()

    mismatch = alice_bases != bob_bases

    bob_bits[mismatch] = np.random.randint(0, 2, size=np.sum(mismatch))

    return bob_bits

def sift_keys(alice_bits, bob_bits, alice_bases, bob_bases):
    matching_positions = alice_bases==bob_bases

    alice_key = alice_bits[matching_positions]
    bob_key = bob_bits[matching_positions]

    return alice_key, bob_key, matching_positions

def calculate_qber(alice_key, bob_key):
    if len(alice_key) == 0:
        return 0.0
    
    errors = np.sum(alice_key!=bob_key)
    return errors/len(alice_key)

def run_bb84_without_eve(n=20):
    alice_bits = generate_random_bits(n)
    alice_bases = generate_random_bases(n)
    bob_bases = generate_random_bases(n)

    bob_bits = bob_measurement(alice_bits, alice_bases, bob_bases)

    alice_key, bob_key, matching_positions = sift_keys(alice_bits, bob_bits, alice_bases, bob_bases)

    qber = calculate_qber(alice_key, bob_key)

    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bits": bob_bits,
        "bob_bases": bob_bases,
        "matching_positions": matching_positions,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "qber": qber
    }
