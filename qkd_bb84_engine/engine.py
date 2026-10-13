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


def measure_qubit(state: List[complex], basis: str, rng=None) -> int:
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
    if (rng or random).random() < prob0:
        return 0
    else:
        return 1


def apply_channel(state: List[complex], noise_prob: float = 0.0,
                   eavesdrop: bool = False, rng=None) -> List[complex]:
    """
    Simulate quantum channel with optional noise and eavesdropping.
    
    noise_prob: probability of bit flip (depolarizing noise)
    eavesdrop: if True, Eve intercepts and resends (introduces ~25% error)
    """
    result = state[:]
    
    # Eavesdropping: Eve measures in random basis and resends
    if eavesdrop:
        eve_basis = (rng or random).choice(['+', 'x'])
        eve_result = measure_qubit(result, eve_basis, rng=rng)
        result = qubit_state(eve_result, eve_basis)
    
    # Noise: simple bit flip channel
    if noise_prob > 0 and (rng or random).random() < noise_prob:
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
        n_qubits: number of qubits to transmit (must be positive)
        noise_prob: channel noise probability (0.0 to 1.0)
        eavesdrop: whether Eve is eavesdropping
        seed: random seed for reproducibility

    Returns dict with protocol results.

    Raises:
        ValueError: if parameters are out of valid range
    """
    if not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError(f"n_qubits must be a positive integer, got {n_qubits}")
    if not (0.0 <= noise_prob <= 1.0):
        raise ValueError(f"noise_prob must be between 0.0 and 1.0, got {noise_prob}")
    if seed is not None and not isinstance(seed, int):
        raise ValueError(f"seed must be an integer or None, got {type(seed).__name__}")
    rng = random.Random(seed) if seed is not None else random
    
    # Step 1: Alice generates random bits and bases
    alice_bits = [rng.randint(0, 1) for _ in range(n_qubits)]
    alice_bases = [rng.choice(['+', 'x']) for _ in range(n_qubits)]
    
    # Step 2: Alice prepares qubits
    alice_qubits = [qubit_state(b, b_) for b, b_ in zip(alice_bits, alice_bases)]
    
    # Step 3: Transmit through channel
    received_qubits = [apply_channel(q, noise_prob, eavesdrop, rng=rng) for q in alice_qubits]
    
    # Step 4: Bob measures in random bases
    bob_bases = [rng.choice(['+', 'x']) for _ in range(n_qubits)]
    bob_bits = [measure_qubit(q, b, rng=rng) for q, b in zip(received_qubits, bob_bases)]
    
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
        sample_indices = rng.sample(range(sifted_key_length), sample_size)
        
        errors_found = 0
        for idx in sample_indices:
            if sifted_alice[idx] != sifted_bob[idx]:
                errors_found += 1
        
        qber = errors_found / sample_size if sample_size > 0 else 0.0
        
        # Remove sampled bits from key
        sampled = set(sample_indices)
        remaining_indices = [i for i in range(sifted_key_length) if i not in sampled]
        final_alice = [sifted_alice[i] for i in remaining_indices]
        final_bob = [sifted_bob[i] for i in remaining_indices]
    
    # This educational simulation has no error-correction stage or security proof.
    # Never expose keys when the channel is unestimated or the raw strings differ.
    if sample_size == 0:
        abort_reason = "Insufficient sifted bits for error estimation"
    elif qber > 0.11:
        abort_reason = "Estimated QBER exceeds the illustrative 11% cutoff"
    elif final_alice != final_bob:
        abort_reason = "Residual key mismatch; error correction is not implemented"
    elif not final_alice:
        abort_reason = "No residual key material"
    else:
        abort_reason = None
    if abort_reason is None:
        final_key_alice = privacy_amplification(final_alice)
        final_key_bob = privacy_amplification(final_bob)
    else:
        final_key_alice = []
        final_key_bob = []
    keys_match = abort_reason is None and final_key_alice == final_key_bob

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
        'aborted': abort_reason is not None,
        'abort_reason': abort_reason,
        'parameter_estimation_possible': sample_size > 0,
        'eavesdrop_detected': sample_size > 0 and qber > 0.11,
        'noise_prob': noise_prob,
        'eavesdrop': eavesdrop,
    }


def privacy_amplification(bits: List[int], output_length: Optional[int] = None) -> List[int]:
    """Educational SHAKE-256 compression, NOT universal-hash QKD privacy amplification."""
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("bits must be 0 or 1")
    if not bits:
        if output_length not in (None, 0):
            raise ValueError("Cannot extract key bits from empty input")
        return []
    if output_length is None:
        output_length = max(1, len(bits) // 2)
    if not isinstance(output_length, int) or not 0 <= output_length <= len(bits):
        raise ValueError("output_length must not exceed input bit count")
    digest = hashlib.shake_256(bytes(bits)).digest((output_length + 7) // 8)
    return [(digest[i // 8] >> (7 - i % 8)) & 1 for i in range(output_length)]


def calculate_key_rate(n_qubits: int, qber: float) -> float:
    """
    Calculate the theoretical key generation rate.

    Rate = max(0, 1 - 2 H(QBER)) (idealized asymptotic bound)
    where H is the binary entropy function.

    Args:
        n_qubits: number of qubits (must be positive)
        qber: quantum bit error rate (0.0 to 1.0)

    Returns:
        Key generation rate (0.0 to 1.0)

    Raises:
        ValueError: if parameters are out of valid range
    """
    if not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError(f"n_qubits must be a positive integer, got {n_qubits}")
    if not (0.0 <= qber <= 1.0):
        raise ValueError(f"qber must be between 0.0 and 1.0, got {qber}")
    # Idealized asymptotic BB84 bound per sifted bit (not finite-key secure).
    if qber >= 0.5:
        return 0.0
    return max(0.0, 1.0 - 2.0 * binary_entropy(qber))


def binary_entropy(p: float) -> float:
    """
    Binary entropy function H(p) = -p*log2(p) - (1-p)*log2(1-p).

    Args:
        p: probability (0.0 to 1.0)

    Returns:
        Binary entropy value (0.0 to 1.0)

    Raises:
        ValueError: if p is out of valid range
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p must be between 0.0 and 1.0, got {p}")
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


# ─── Eavesdropping Analysis ─────────────────────────────────────────────────

def eavesdrop_analysis(n_qubits: int = 1000, n_trials: int = 10,
                        seed: int = 42) -> dict:
    """
    Analyze the effect of eavesdropping on QBER.

    Runs multiple trials with and without eavesdropping to compare QBER.

    Args:
        n_qubits: number of qubits per trial (must be positive)
        n_trials: number of trials to run (must be positive)
        seed: random seed for reproducibility

    Returns:
        Dict with analysis results

    Raises:
        ValueError: if parameters are out of valid range
    """
    if not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError(f"n_qubits must be a positive integer, got {n_qubits}")
    if not isinstance(n_trials, int) or n_trials < 1:
        raise ValueError(f"n_trials must be a positive integer, got {n_trials}")
    rng = random.Random(seed)
    
    no_eve_qbers = []
    eve_qbers = []
    
    for trial in range(n_trials):
        # Without eavesdropping
        result_no_eve = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=False, seed=rng.randrange(2**63))
        if result_no_eve['sample_size'] > 0:
            no_eve_qbers.append(result_no_eve['qber'])
        
        # With eavesdropping
        result_eve = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=True, seed=rng.randrange(2**63))
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

    Args:
        n_qubits: number of qubits per trial (must be positive)
        n_trials: number of trials to run (must be positive)
        seed: random seed for reproducibility

    Returns:
        Dict with statistics results

    Raises:
        ValueError: if parameters are out of valid range
    """
    if not isinstance(n_qubits, int) or n_qubits < 1:
        raise ValueError(f"n_qubits must be a positive integer, got {n_qubits}")
    if not isinstance(n_trials, int) or n_trials < 1:
        raise ValueError(f"n_trials must be a positive integer, got {n_trials}")
    rng = random.Random(seed)
    
    sifted_lengths = []
    qbers = []
    key_lengths = []
    detection_rates = []
    
    for _ in range(n_trials):
        result = bb84_protocol(n_qubits, noise_prob=0.0, eavesdrop=False, seed=rng.randrange(2**63))
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


class FrontierDomainEngine:
    """Legacy generic metric evaluator (independent of the BB84 simulation)."""

    @staticmethod
    def evaluate_primary_parameter(value):
        if value > 25:
            return {
                "summary": "Primary metric above threshold",
                "details": f"Primary metric {value} exceeds 25",
                "remediation": "Review the metric and threshold",
            }
        return None

    @staticmethod
    def evaluate_secondary_kinetics(value, critical_flag):
        if critical_flag or value > 12:
            return {
                "summary": "Secondary metric escalation",
                "details": f"Secondary metric {value}; critical flag {critical_flag}",
                "remediation": "Review secondary metric and escalation flag",
            }
        return None

    @staticmethod
    def audit_specification_conformance(status, attributes):
        if any(token in str(status).upper() for token in ("DISCORDANT", "ANOMALY", "FAIL", "REJECT")):
            return {
                "summary": "Descriptor anomaly",
                "details": f"Descriptor: {status}",
                "remediation": "Review the descriptor",
            }
        return None
