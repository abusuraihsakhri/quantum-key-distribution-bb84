# Quantum Key Distribution BB84

> **Domain:** Post-Quantum Cryptography & Quantum Key Distribution
> **Standards:** ETSI QKD GS 004, NIST FIPS 203/204/205

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

A real implementation of the BB84 Quantum Key Distribution protocol using state vector simulation. This project simulates quantum cryptography including:

- **BB84 Protocol**: Full simulation of qubit preparation, transmission, measurement, sifting, and privacy amplification
- **Eavesdropping Detection**: Analysis of QBER (Quantum Bit Error Rate) to detect Eve
- **Decoy State BB84**: Protection against photon-number-splitting attacks
- **Finite-Key Analysis**: Composable security bounds for practical implementations
- **FastAPI REST API**: Web interface for audit and chat operations
- **HMAC-SHA256 Audit Trail**: Tamper-evident cryptographic logging

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Quantum State Preparation**: Rectilinear (+) and diagonal (x) basis states
- **BB84 Protocol Engine**: Complete protocol simulation with noise and eavesdropping
- **Privacy Amplification**: SHA-256 based universal hashing
- **Key Rate Calculation**: Theoretical key generation rate with binary entropy
- **Eavesdropping Analysis**: Statistical comparison of QBER with/without Eve
- **Multi-Agent Supervisor**: Invariant QC, Safety Escalation, and Protocol Conformance workers
- **PHI Guard**: HIPAA Safe Harbor compliant outbound data protection
- **Prometheus Metrics**: Operational telemetry export

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/quantum-key-distribution-bb84.git
cd quantum-key-distribution-bb84

# Install dependencies
pip install -e .

# For web server functionality
pip install fastapi uvicorn

# For testing
pip install pytest
```

---

## 💻 CLI Quickstart & Usage

### 1. Run BB84 Protocol
```bash
python cli.py run --qubits 100 --seed 42
python cli.py run --qubits 500 --eavesdrop --show-key
python cli.py run --qubits 200 --noise 0.05 --show-sifted
```

### 2. Analyze Eavesdropping
```bash
python cli.py eavesdrop --qubits 500 --trials 10
```

### 3. Protocol Statistics
```bash
python cli.py stats --qubits 200 --trials 50
```

### 4. Key Rate Calculation
```bash
python cli.py rate --qubits 1000 --qber 0.05
```

### 5. Supervisor Audit
```bash
python cli.py audit --task-id "TASK-001" --primary-metric 15.0
python cli.py chat "Explain BB84 protocol"
python cli.py verify-audit
```

### 6. Start Web Server
```bash
# Set audit secret key first
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

python cli.py serve --host 0.0.0.0 --port 8000
```

### Parameter Reference
- `--qubits`: Number of qubits to transmit (positive integer)
- `--noise`: Channel noise probability (0.0 to 1.0)
- `--eavesdrop`: Enable eavesdropping simulation
- `--seed`: Random seed for reproducibility
- `--show-key`: Display final keys
- `--show-sifted`: Display sifted keys (first 50 bits)
- `--trials`: Number of trials for analysis
- `--qber`: Quantum bit error rate for rate calculation

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Secure Key Management:** Audit secret key must be provided via `AUDIT_SECRET_KEY` environment variable (minimum 16 characters).
* **FastAPI REST API:** OpenAPI 3.1 endpoints for audit, chat, and metrics.
* **Prometheus Telemetry:** Operational metrics at `/metrics`.

### Security Requirements

The `AUDIT_SECRET_KEY` environment variable is **required** for audit operations. Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Set a test key
export AUDIT_SECRET_KEY=test-audit-key-for-development-only-2026

# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=qkd_bb84_engine --cov=agents
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker-compose up --build

# Or with Docker directly
docker build -t quantum-key-distribution-bb84 .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=${AUDIT_SECRET_KEY} quantum-key-distribution-bb84
```

---

## 📁 Project Structure

```
quantum-key-distribution-bb84/
├── agents/                  # Multi-agent supervisor system
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Orchestrator for agent workers
│   ├── workers.py          # Specialized domain workers
│   ├── llm_factory.py      # LLM client factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics collector
│   └── streamer.py         # WebSocket telemetry broadcaster
├── qkd_bb84_engine/        # Core QKD engine
│   ├── engine.py           # BB84 protocol implementation
│   ├── models.py           # Engine data models
│   └── server.py           # Engine server module
├── tests/                  # Test suite
│   ├── test_qkd_bb84_engine.py
│   ├── test_quantum_key_distribution_bb84.py
│   └── test_enrichment.py
├── web/index.html          # Operations console UI
├── cli.py                  # Command-line interface
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Enrichment feature implementations
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container definition
└── docker-compose.yml      # Multi-container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
