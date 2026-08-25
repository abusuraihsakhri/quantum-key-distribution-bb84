"""
BB84 Quantum Key Distribution Engine
Real implementation using state vector simulation with Python stdlib only.

BB84 Protocol (Bennett & Brassard, 1984):
1. Alice prepares random qubits in random bases (rectilinear + or diagonal ×)
2. Qubits are transmitted through quantum channel
3. Bob measures each qubit in a random basis
4. Alice and Bob publicly compare bases (sifting)
5. They sacrifice a subset to estimate error rate (QBER)
6. If QBER < threshold (~11%), proceed with privacy amplification
7. Final key is the remaining sifted bits after error correction and privacy amplification

Eavesdropping detection: Any eavesdropper (Eve) introduces ~25% error rate
because she must guess the basis for each qubit.
"""
import cmath
import math
import random
import hashlib
from typing import List, Tuple, Dict, Optional


# ─── Gate Matrices ───────────────────────────────────────────────────────────

SQRT2_INV = 1.0 / math.sqrt(2.0)

H_MATRIX = [
    [complex(SQRT2_INV, 0), complex(SQRT2_INV, 0)],
    [complex(SQRT2_INV, 0), complex(-SQRT2_INV, 0)],
]

I_MATRIX = [
    [complex(1, 0), complex(0, 0)],
    [complex(0, 0), complex(1, 0)],
]

X_MATRIX = [
    [complex(0, 0), complex(1, 0)],
    [complex(1, 0), complex(0, 0)],
]


# ─── State Vector Operations ────────────────────────────────────────────────

def qubit_state(bit: int, basis: str) -> List[complex]:
    """
    Prepare a qubit state.
    
    bit: 0 or 1
    basis: '+' (rectilinear) or 'x' (diagonal)
    
    Rectilinear basis:
        |0⟩ → |0⟩, |1⟩ → |1⟩
    Diagonal basis:
        |0⟩ → |+⟩ = 1/√2(|0⟩ + |1⟩), |1⟩ → |−⟩ = 1/√2(|0⟩ - |1⟩)
    """
    if basis == '+':
        if bit == 0:
            return [complex(1, 0), complex(0, 0)]
        else:
            return [complex(0, 0), complex(1, 0)]
    elif basis == 'x':
        if bit == 0:
            return [complex(SQRT2_INV, 0), complex(SQRT2_INV, 0)]
        else:
            return [complex(SQRT2_INV, 0), complex(-SQRT2_INV, 0)]
    else:
        raise ValueError(f"Unknown basis: {basis}")


def measure_qubit(state: List[complex], basis: str) -> int:
    """
    Measure a qubit in the given basis.
    
    Returns 0 or 1 based on Born rule probabilities.
    """
    if basis == '+':
        # Measure in computational basis
        prob0 = abs(state[0]) ** 2
    elif basis == 'x':
        # Measure in diagonal basis: project onto |+⟩ and |−⟩
        # ⟨+|ψ⟩ = (⟨0| + ⟨1|)/√2 · |ψ⟩
        amp_plus = SQRT2_INV * (state[0] + state[1])
        prob0 = abs(amp_plus) ** 2
    else:
        raise ValueError(f"Unknown basis: {basis}")
    
    # Born rule: collapse to |0⟩ or |1⟩ in measurement basis
    if random.random() < prob0:
        return 0
    else:
        return 1


def apply_channel(state: List[complex], noise_prob: float = 0.0,
                   eavesdrop: bool = False) -> List[complex]:
    """
    Simulate quantum channel with optional noise and eavesdropping.
    
    noise_prob: probability of bit flip (depolarizing noise)
    eavesdrop: if True, Eve intercepts and resends (introduces ~25% error)
    """
    result = state[:]
    
    # Eavesdropping: Eve measures in random basis and resends
    if eavesdrop:
        eve_basis = random.choice(['+', 'x'])
        eve_result = measure_qubit(result, eve_basis)
        result = qubit_state(eve_result, eve_basis)
    
    # Noise: simple bit flip channel
    if noise_prob > 0 and random.random() < noise_prob:
        result = apply_x_gate(result)
    
    return result


def apply_x_gate(state: List[complex]) -> List[complex]:
    """Apply Pauli-X (bit flip) gate."""
    return [state[1], state[0]]


def apply_h_gate(state: List[complex]) -> List[complex]:
    """Apply Hadamard gate."""
    return [
        SQRT2_INV * (state[0] + state[1]),
        SQRT2_INV * (state[0] - state[1]),
    ]


# ─── BB84 Protocol ──────────────────────────────────────────────────────────

def bb84_protocol(n_qubits: int, noise_prob: float = 0.0,
                   eavesdrop: bool = False, seed: Optional[int] = None) -> dict:
    """
    Execute the full BB84 protocol.
    
    Args:
        n_qubits: number of qubits to transmit
        noise_prob: channel noise probability
        eavesdrop: whether Eve is eavesdropping
        seed: random seed for reproducibility
    
    Returns dict with protocol results.
    """
    if seed is not None:
        random.seed(seed)
    
    # Step 1: Alice generates random bits and bases
    alice_bits = [random.randint(0, 1) for _ in range(n_qubits)]
    alice_bases = [random.choice(['+', 'x']) for _ in range(n_qubits)]
    
    # Step 2: Alice prepares qubits
    alice_qubits = [qubit_state(b, b_) for b, b_ in zip(alice_bits, alice_bases)]
    
    # Step 3: Transmit through channel
    received_qubits = [apply_channel(q, noise_prob, eavesdrop) for q in alice_qubits]
    
    # Step 4: Bob measures in random bases
    bob_bases = [random.choice(['+', 'x']) for _ in range(n_qubits)]
    bob_bits = [measure_qubit(q, b) for q, b in zip(received_qubits, bob_bases)]
    
    # Step 5: Basis reconciliation (sifting)
    sifted_alice = []
    sifted_bob = []
    matching_indices = []
    for i in range(n_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])
            matching_indices.append(i)
    
    sifted_key_length = len(sifted_alice)
    
    # Step 6: Error estimation (sacrifice half of sifted bits)
    if sifted_key_length < 10:
        # Not enough bits for meaningful error estimation
        qber = 0.0
        errors_found = 0
        sample_size = 0
        final_alice = sifted_alice
        final_bob = sifted_bob
    else:
        sample_size = sifted_key_length // 2
        sample_indices = random.sample(range(sifted_key_length), sample_size)
        
        errors_found = 0
        for idx in sample_indices:
            if sifted_alice[idx] != sifted_bob[idx]:
                errors_found += 1
        
        qber = errors_found / sample_size if sample_size > 0 else 0.0
        
        # Remove sampled bits from key
        remaining_indices = [i for i in range(sifted_key_length) if i not in set(sample_indices)]
        final_alice = [sifted_alice[i] for i in remaining_indices]
        final_bob = [sifted_bob[i] for i in remaining_indices]
    
    # Step 7: Privacy amplification (simplified - hash-based)
    if len(final_alice) > 0:
        final_key_alice = privacy_amplification(final_alice)
        final_key_bob = privacy_amplification(final_bob)
    else:
        final_key_alice = []
        final_key_bob = []
    
    # Check if keys match
    keys_match = final_key_alice == final_key_bob
    
    return {
        'n_qubits': n_qubits,
        'alice_bits': alice_bits,
        'alice_bases': alice_bases,
        'bob_bases': bob_bases,
        'bob_bits': bob_bits,
        'matching_bases': len(matching_indices),
        'matching_indices': matching_indices,
        'sifted_key_length': sifted_key_length,
        'sifted_alice': sifted_alice,
        'sifted_bob': sifted_bob,
        'sample_size': sample_size,
        'errors_found': errors_found,
        'qber': qber,
        'final_key_alice': final_key_alice,
        'final_key_bob': final_key_bob,
        'final_key_length': len(final_key_alice),
        'keys_match': keys_match,
        'eavesdrop_detected': qber > 0.11,
        'noise_prob': noise_prob,
        'eavesdrop': eavesdrop,
    }


def privacy_amplification(bits: List[int], output_length: Optional[int] = None) -> List[int]:
    """
    Privacy amplification using universal hashing.
    
    Reduces the key length to remove potential information leaked to Eve.
    Uses a simple hash function based on XOR of subsets.
    """
    if not bits:
        return []
    
    if output_length is None:
        output_length = max(1, len(bits) // 2)
    
    # Convert bits to bytes for hashing
    bit_string = ''.join(str(b) for b in bits)
    byte_data = bit_string.encode('utf-8')
    
    # Use SHA-256 hash
    hash_obj = hashlib.sha256(byte_data)
    hash_bytes = hash_obj.digest()
    
    # Extract output_length bits from hash
    result = []
    for i in range(output_length):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(hash_bytes):
            result.append((hash_bytes[byte_idx] >> (7 - bit_idx)) & 1)
        else:
            result.append(0)
    
    return result


def calculate_key_rate(n_qubits: int, qber: float) -> float:
    """
    Calculate the theoretical key generation rate.
    
    Rate = 1 - H(QBER) - QBER * log2(3)
    where H is the binary entropy function.
    """
    if qber <= 0 or qber >= 1:
        return 0.0
    
    # Binary entropy
    h = -qber * math.log2(qber) - (1 - qber) * math.log2(1 - qber)
    
    # Key rate (simplified)
    rate = max(0, 1 - h - qber * math.log2(3))
    
    return rate


def binary_entropy(p: float) -> float:
    """Binary entropy function H(p) = -p*log2(p) - (1-p)*log2(1-p)."""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


# ─── Eavesdropping Analysis ─────────────────────────────────────────────────

def eavesdrop_analysis(n_qubits: int = 1000, n_trials: int = 10,
                        seed: int = 42) -> dict:
    """
    Analyze the effect of eavesdropping on QBER.
    
    Runs multiple trials with and without eavesdropping to compare QBER.
    """
    random.seed(seed)
    
    no_eve_qbers = []
    eve_qbers = []
    
    for trial in range(n_trials):
        # Without eavesdropping
        result_no_eve = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=False)
        if result_no_eve['sample_size'] > 0:
            no_eve_qbers.append(result_no_eve['qber'])
        
        # With eavesdropping
        result_eve = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=True)
        if result_eve['sample_size'] > 0:
            eve_qbers.append(result_eve['qber'])
    
    avg_no_eve = sum(no_eve_qbers) / len(no_eve_qbers) if no_eve_qbers else 0
    avg_eve = sum(eve_qbers) / len(eve_qbers) if eve_qbers else 0
    
    return {
        'n_qubits': n_qubits,
        'n_trials': n_trials,
        'avg_qber_no_eavesdrop': avg_no_eve,
        'avg_qber_with_eavesdrop': avg_eve,
        'eavesdrop_threshold': 0.11,
        'no_eve_detected': avg_no_eve > 0.11,
        'eve_detected': avg_eve > 0.11,
        'distinguishable': avg_eve > avg_no_eve + 0.05,
    }


# ─── Protocol Statistics ────────────────────────────────────────────────────

def protocol_statistics(n_qubits: int = 1000, n_trials: int = 100,
                         seed: int = 42) -> dict:
    """
    Gather statistics over multiple BB84 protocol runs.
    """
    random.seed(seed)
    
    sifted_lengths = []
    qbers = []
    key_lengths = []
    detection_rates = []
    
    for _ in range(n_trials):
        result = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=False)
        sifted_lengths.append(result['sifted_key_length'])
        if result['sample_size'] > 0:
            qbers.append(result['qber'])
        key_lengths.append(result['final_key_length'])
        detection_rates.append(1 if result['eavesdrop_detected'] else 0)
    
    return {
        'n_qubits': n_qubits,
        'n_trials': n_trials,
        'avg_sifted_length': sum(sifted_lengths) / len(sifted_lengths),
        'avg_qber': sum(qbers) / len(qbers) if qbers else 0,
        'avg_key_length': sum(key_lengths) / len(key_lengths),
        'false_alarm_rate': sum(detection_rates) / len(detection_rates),
        'theoretical_sifted_fraction': 0.5,  # ~50% of bases match
    }
