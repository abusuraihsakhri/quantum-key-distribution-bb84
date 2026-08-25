# BB84 Quantum Key Distribution

Real implementation of the BB84 QKD protocol (Bennett & Brassard, 1984) using state vector simulation in pure Python (stdlib only).

## What This Actually Does

- **Qubit preparation** — random basis choice (rectilinear + or diagonal ×)
- **Qubit transmission** — simulated quantum channel with optional noise
- **Basis reconciliation** — sifting step discarding mismatched bases
- **Error estimation** — sample comparison to compute QBER
- **Privacy amplification** — SHA-256 hash-based key compression
- **Eavesdropping detection** — QBER threshold (~11%)
- **Key rate calculation** — theoretical secure key rate

### Protocol Steps

1. Alice prepares random qubits in random bases (+ or ×)
2. Qubits transmitted through quantum channel
3. Bob measures each qubit in a random basis
4. Alice and Bob compare bases publicly (sifting)
5. Sacrifice subset to estimate QBER
6. If QBER < 11%, apply privacy amplification → secure key

### Eavesdropping Detection

Without Eve: QBER ≈ 0% (only channel noise)
With Eve: QBER ≈ 25% (Eve must guess basis for each qubit)

## Usage

```bash
# Run BB84 with 100 qubits
python cli.py run -n 100 --show-key

# Run with eavesdropping
python cli.py run -n 200 --eavesdrop --show-key

# Analyze eavesdropping detection
python cli.py eavesdrop -n 500 --trials 10

# Protocol statistics
python cli.py stats -n 200 --trials 50

# Key rate calculation
python cli.py rate --qber 0.05
```

## API

```python
from qkd_bb84_engine.engine import bb84_protocol, eavesdrop_analysis

# Single protocol run
result = bb84_protocol(n_qubits=100, eavesdrop=False, seed=42)
print(f"QBER: {result['qber']}, Key length: {result['final_key_length']}")

# Eavesdropping analysis
analysis = eavesdrop_analysis(n_qubits=1000, n_trials=10)
print(f"Avg QBER with Eve: {analysis['avg_qber_with_eavesdrop']}")
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Limitations

- Simulated quantum channel (no real quantum hardware)
- Privacy amplification uses SHA-256 (simplified)
- No error correction step (assumed perfect after sifting)
- Single-photon source assumed (no decoy states)
