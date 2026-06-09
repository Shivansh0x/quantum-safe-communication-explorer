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

def apply_channel_noise(bits, noise_probability):
    """
    Apply simple bit-flip channel noise.

    Each transmitted bit flips with probability noise_probability.
    This models a simplified noisy quantum channel at the protocol level.
    """
    if noise_probability < 0 or noise_probability > 1:
        raise ValueError("noise_probability must be between 0 and 1.")

    noisy_bits = bits.copy()
    noise_mask = np.random.random(size=len(bits)) < noise_probability

    noisy_bits[noise_mask] = 1 - noisy_bits[noise_mask]

    return noisy_bits, noise_mask

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

def run_bb84_with_eve(n=1000, eve_intercept_prob=0.25, channel_noise_prob=0.0):
    alice_bits = generate_random_bits(n)
    alice_bases = generate_random_bases(n)

    eve_intercepts = np.random.random(size=n) < eve_intercept_prob
    eve_bases = generate_random_bases(n)

    transmitted_bits = alice_bits.copy()
    transmitted_bases = alice_bases.copy()

    for i in range(n):
        if eve_intercepts[i]:
            if eve_bases[i] == alice_bases[i]:
                eve_bit = alice_bits[i]
            else:
                eve_bit = np.random.randint(0, 2)
            
            transmitted_bits[i] = eve_bit
            transmitted_bases[i] = eve_bases[i]
    
    transmitted_bits, channel_noise_mask = apply_channel_noise(
        transmitted_bits,
        noise_probability = channel_noise_prob
    )

    bob_bases = generate_random_bases(n)
    bob_bits = bob_measurement(transmitted_bits, transmitted_bases, bob_bases)

    alice_key, bob_key, matching_positions = sift_keys(alice_bits, bob_bits, alice_bases, bob_bases)

    qber = calculate_qber(alice_key, bob_key)

    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "eve_intercepts": eve_intercepts,
        "eve_bases": eve_bases,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "matching_positions": matching_positions,
        "qber": qber,
        "eve_intercept_prob": eve_intercept_prob,
        "channel_noise_prob": channel_noise_prob,
        "channel_noise_mask": channel_noise_mask
    }