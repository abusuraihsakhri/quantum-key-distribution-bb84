"""
Tests for BB84 Quantum Key Distribution Engine.
Real QKD protocol verification.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import math
import random
import pytest
from qkd_bb84_engine.engine import (
    qubit_state, measure_qubit, apply_channel, apply_x_gate, apply_h_gate,
    bb84_protocol, privacy_amplification, calculate_key_rate,
    binary_entropy, eavesdrop_analysis, protocol_statistics,
)


# ─── Qubit State Preparation ────────────────────────────────────────────────

class TestQubitState:
    def test_rectilinear_zero(self):
        state = qubit_state(0, '+')
        assert abs(state[0] - 1.0) < 1e-10
        assert abs(state[1]) < 1e-10

    def test_rectilinear_one(self):
        state = qubit_state(1, '+')
        assert abs(state[0]) < 1e-10
        assert abs(state[1] - 1.0) < 1e-10

    def test_diagonal_zero(self):
        state = qubit_state(0, 'x')
        assert abs(state[0] - 1 / math.sqrt(2)) < 1e-10
        assert abs(state[1] - 1 / math.sqrt(2)) < 1e-10

    def test_diagonal_one(self):
        state = qubit_state(1, 'x')
        assert abs(state[0] - 1 / math.sqrt(2)) < 1e-10
        assert abs(state[1] + 1 / math.sqrt(2)) < 1e-10

    def test_states_normalized(self):
        for bit in [0, 1]:
            for basis in ['+', 'x']:
                state = qubit_state(bit, basis)
                norm_sq = abs(state[0]) ** 2 + abs(state[1]) ** 2
                assert abs(norm_sq - 1.0) < 1e-10

    def test_invalid_basis(self):
        with pytest.raises(ValueError):
            qubit_state(0, 'y')


# ─── Measurement ─────────────────────────────────────────────────────────────

class TestMeasurement:
    def test_measure_zero_in_rectilinear(self):
        random.seed(42)
        state = qubit_state(0, '+')
        # Measuring |0⟩ in + basis should always give 0
        results = [measure_qubit(state, '+') for _ in range(100)]
        assert all(r == 0 for r in results)

    def test_measure_one_in_rectilinear(self):
        random.seed(42)
        state = qubit_state(1, '+')
        results = [measure_qubit(state, '+') for _ in range(100)]
        assert all(r == 1 for r in results)

    def test_measure_plus_in_diagonal(self):
        random.seed(42)
        state = qubit_state(0, 'x')  # |+⟩
        results = [measure_qubit(state, 'x') for _ in range(100)]
        assert all(r == 0 for r in results)

    def test_measure_minus_in_diagonal(self):
        random.seed(42)
        state = qubit_state(1, 'x')  # |−⟩
        results = [measure_qubit(state, 'x') for _ in range(100)]
        assert all(r == 1 for r in results)

    def test_measure_wrong_basis_gives_random(self):
        random.seed(42)
        state = qubit_state(0, '+')  # |0⟩
        # Measuring in diagonal basis gives 50/50
        results = [measure_qubit(state, 'x') for _ in range(1000)]
        count0 = sum(1 for r in results if r == 0)
        assert 400 < count0 < 600  # ~50%

    def test_invalid_measurement_basis(self):
        with pytest.raises(ValueError):
            measure_qubit([1, 0], 'y')


# ─── Gates ───────────────────────────────────────────────────────────────────

class TestGates:
    def test_x_gate_flips(self):
        state = [complex(1, 0), complex(0, 0)]
        result = apply_x_gate(state)
        assert abs(result[0]) < 1e-10
        assert abs(result[1] - 1.0) < 1e-10

    def test_h_gate_on_zero(self):
        state = [complex(1, 0), complex(0, 0)]
        result = apply_h_gate(state)
        assert abs(result[0] - 1 / math.sqrt(2)) < 1e-10
        assert abs(result[1] - 1 / math.sqrt(2)) < 1e-10

    def test_h_gate_on_one(self):
        state = [complex(0, 0), complex(1, 0)]
        result = apply_h_gate(state)
        assert abs(result[0] - 1 / math.sqrt(2)) < 1e-10
        assert abs(result[1] + 1 / math.sqrt(2)) < 1e-10


# ─── Channel ─────────────────────────────────────────────────────────────────

class TestChannel:
    def test_noiseless_channel(self):
        random.seed(42)
        state = qubit_state(0, '+')
        received = apply_channel(state, noise_prob=0.0, eavesdrop=False)
        assert abs(received[0] - state[0]) < 1e-10
        assert abs(received[1] - state[1]) < 1e-10

    def test_eavesdrop_introduces_error(self):
        random.seed(42)
        # Send |0⟩ through eavesdropped channel many times
        errors = 0
        n_trials = 1000
        for _ in range(n_trials):
            state = qubit_state(0, '+')
            received = apply_channel(state, noise_prob=0.0, eavesdrop=True)
            # Measure in correct basis
            result = measure_qubit(received, '+')
            if result != 0:
                errors += 1
        # Eve should introduce ~25% error
        error_rate = errors / n_trials
        assert 0.15 < error_rate < 0.35


# ─── BB84 Protocol ───────────────────────────────────────────────────────────

class TestBB84Protocol:
    def test_protocol_returns_all_fields(self):
        result = bb84_protocol(100, seed=42)
        required = ['n_qubits', 'alice_bits', 'alice_bases', 'bob_bases',
                     'bob_bits', 'matching_bases', 'sifted_key_length',
                     'sifted_alice', 'sifted_bob', 'qber', 'final_key_alice',
                     'final_key_bob', 'final_key_length', 'keys_match',
                     'eavesdrop_detected']
        for key in required:
            assert key in result

    def test_matching_bases_approximately_half(self):
        random.seed(42)
        result = bb84_protocol(1000, seed=42)
        # ~50% of bases should match
        ratio = result['matching_bases'] / result['n_qubits']
        assert 0.4 < ratio < 0.6

    def test_no_noise_no_eavesdrop_low_qber(self):
        result = bb84_protocol(500, noise_prob=0.0, eavesdrop=False, seed=42)
        if result['sample_size'] > 0:
            assert result['qber'] < 0.05

    def test_eavesdrop_increases_qber(self):
        result_no_eve = bb84_protocol(1000, eavesdrop=False, seed=42)
        result_eve = bb84_protocol(1000, eavesdrop=True, seed=42)
        if result_no_eve['sample_size'] > 0 and result_eve['sample_size'] > 0:
            assert result_eve['qber'] > result_no_eve['qber']

    def test_keys_match_no_eavesdrop(self):
        result = bb84_protocol(500, noise_prob=0.0, eavesdrop=False, seed=42)
        assert result['keys_match']

    def test_eavesdrop_detected_with_eve(self):
        result = bb84_protocol(1000, eavesdrop=True, seed=42)
        # With Eve, QBER should be high enough to detect
        if result['sample_size'] > 10:
            assert result['eavesdrop_detected']

    def test_sifted_key_shorter_than_original(self):
        result = bb84_protocol(100, seed=42)
        assert result['sifted_key_length'] <= result['n_qubits']

    def test_final_key_shorter_than_sifted(self):
        result = bb84_protocol(500, seed=42)
        assert result['final_key_length'] <= result['sifted_key_length']

    def test_noise_increases_qber(self):
        result_clean = bb84_protocol(1000, noise_prob=0.0, eavesdrop=False, seed=42)
        result_noisy = bb84_protocol(1000, noise_prob=0.1, eavesdrop=False, seed=42)
        if result_clean['sample_size'] > 0 and result_noisy['sample_size'] > 0:
            assert result_noisy['qber'] > result_clean['qber']


# ─── Privacy Amplification ──────────────────────────────────────────────────

class TestPrivacyAmplification:
    def test_pa_reduces_length(self):
        bits = [random.randint(0, 1) for _ in range(100)]
        result = privacy_amplification(bits)
        assert len(result) < len(bits)

    def test_pa_output_is_bits(self):
        bits = [random.randint(0, 1) for _ in range(50)]
        result = privacy_amplification(bits)
        assert all(b in [0, 1] for b in result)

    def test_pa_deterministic(self):
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        result1 = privacy_amplification(bits)
        result2 = privacy_amplification(bits)
        assert result1 == result2

    def test_pa_empty_input(self):
        result = privacy_amplification([])
        assert result == []

    def test_pa_custom_length(self):
        bits = [random.randint(0, 1) for _ in range(100)]
        result = privacy_amplification(bits, output_length=10)
        assert len(result) == 10


# ─── Key Rate ────────────────────────────────────────────────────────────────

class TestKeyRate:
    def test_zero_qber_gives_positive_rate(self):
        rate = calculate_key_rate(1000, 0.001)
        assert rate > 0

    def test_high_qber_gives_zero_rate(self):
        rate = calculate_key_rate(1000, 0.25)
        assert rate == 0.0

    def test_threshold_qber(self):
        # At ~11% QBER, key rate should be near zero
        rate = calculate_key_rate(1000, 0.11)
        assert rate >= 0

    def test_binary_entropy_symmetric(self):
        assert abs(binary_entropy(0.1) - binary_entropy(0.9)) < 1e-10

    def test_binary_entropy_max(self):
        assert abs(binary_entropy(0.5) - 1.0) < 1e-10

    def test_binary_entropy_zero(self):
        assert binary_entropy(0.0) == 0.0
        assert binary_entropy(1.0) == 0.0


# ─── Eavesdrop Analysis ─────────────────────────────────────────────────────

class TestEavesdropAnalysis:
    def test_analysis_returns_fields(self):
        result = eavesdrop_analysis(200, n_trials=3, seed=42)
        assert 'avg_qber_no_eavesdrop' in result
        assert 'avg_qber_with_eavesdrop' in result
        assert 'eve_detected' in result

    def test_eve_qber_higher(self):
        result = eavesdrop_analysis(500, n_trials=5, seed=42)
        assert result['avg_qber_with_eavesdrop'] > result['avg_qber_no_eavesdrop']


# ─── CLI Tests ───────────────────────────────────────────────────────────────

class TestCLI:
    def test_run_command(self):
        from cli import main
        assert main(["run", "-n", "100", "--seed", "42"]) == 0

    def test_run_with_eavesdrop(self):
        from cli import main
        assert main(["run", "-n", "200", "--eavesdrop", "--seed", "42"]) == 0

    def test_run_show_key(self):
        from cli import main
        assert main(["run", "-n", "200", "--show-key", "--seed", "42"]) == 0

    def test_eavesdrop_command(self):
        from cli import main
        assert main(["eavesdrop", "-n", "200", "--trials", "3", "--seed", "42"]) == 0

    def test_stats_command(self):
        from cli import main
        assert main(["stats", "-n", "100", "--trials", "5", "--seed", "42"]) == 0

    def test_rate_command(self):
        from cli import main
        assert main(["rate", "--qber", "0.05"]) == 0

    def test_audit_command(self):
        from cli import main
        assert main(["audit", "--task-id", "TEST-001"]) == 0

    def test_chat_command(self):
        from cli import main
        assert main(["chat", "Explain", "BB84"]) == 0

    def test_verify_audit_command(self):
        from cli import main
        assert main(["verify-audit"]) == 0

    def test_serve_command_help(self):
        from cli import main
        with pytest.raises(SystemExit):
            main(["serve", "--help"])


# ─── Input Validation Tests ────────────────────────────────────────────────

class TestInputValidation:
    def test_bb84_negative_qubits_raises(self):
        with pytest.raises(ValueError, match="n_qubits must be a positive integer"):
            bb84_protocol(-1)

    def test_bb84_zero_qubits_raises(self):
        with pytest.raises(ValueError, match="n_qubits must be a positive integer"):
            bb84_protocol(0)

    def test_bb84_noise_out_of_range_raises(self):
        with pytest.raises(ValueError, match="noise_prob must be between 0.0 and 1.0"):
            bb84_protocol(100, noise_prob=1.5)

    def test_bb84_negative_noise_raises(self):
        with pytest.raises(ValueError, match="noise_prob must be between 0.0 and 1.0"):
            bb84_protocol(100, noise_prob=-0.1)

    def test_bb84_invalid_seed_raises(self):
        with pytest.raises(ValueError, match="seed must be an integer"):
            bb84_protocol(100, seed="not-a-seed")

    def test_calculate_key_rate_negative_qubits_raises(self):
        with pytest.raises(ValueError, match="n_qubits must be a positive integer"):
            calculate_key_rate(-1, 0.05)

    def test_calculate_key_rate_qber_out_of_range_raises(self):
        with pytest.raises(ValueError, match="qber must be between 0.0 and 1.0"):
            calculate_key_rate(100, 1.5)

    def test_binary_entropy_out_of_range_raises(self):
        with pytest.raises(ValueError, match="p must be between 0.0 and 1.0"):
            binary_entropy(1.5)

    def test_binary_entropy_negative_raises(self):
        with pytest.raises(ValueError, match="p must be between 0.0 and 1.0"):
            binary_entropy(-0.1)

    def test_eavesdrop_analysis_negative_qubits_raises(self):
        with pytest.raises(ValueError, match="n_qubits must be a positive integer"):
            eavesdrop_analysis(n_qubits=-1)

    def test_eavesdrop_analysis_zero_trials_raises(self):
        with pytest.raises(ValueError, match="n_trials must be a positive integer"):
            eavesdrop_analysis(n_trials=0)

    def test_protocol_statistics_negative_qubits_raises(self):
        with pytest.raises(ValueError, match="n_qubits must be a positive integer"):
            protocol_statistics(n_qubits=-1)

    def test_protocol_statistics_zero_trials_raises(self):
        with pytest.raises(ValueError, match="n_trials must be a positive integer"):
            protocol_statistics(n_trials=0)
