# BB84 Quantum Key Distribution Simulator

An educational BB84 quantum key distribution (QKD) simulation implemented with Python's standard library. It models the preparation and measurement of single-qubit state vectors, random measurement bases, basis sifting, intercept-and-resend eavesdropping, a Pauli-X noise channel, and estimation of the quantum bit error rate (QBER).

The repository includes a browser interface, Python CLI, automated tests, and a separate rule-based audit demonstration with a FastAPI backend.

> **Security limitation:** This is **not a cryptographically secure key-distribution implementation**. There is no authenticated classical channel, information reconciliation, composable finite-key bound, decoy-state protocol, or universal-hash privacy amplification. SHAKE-256 is used as *educational compression only*. Never use generated bits for encryption, credentials, or real key exchange. An 11% observed-QBER cutoff is illustrative, not a security guarantee.

## Features

- BB84 state preparation in rectilinear and diagonal bases, measurement and sifting.
- Intercept-and-resend Eve model and independent probabilistic channel noise.
- Randomly disclosed sample for QBER estimation, with demonstrated key generation aborted when errors remain or the sample is insufficient.
- Idealized asymptotic BB84 bound `max(0, 1 − 2 h₂(QBER))` per sifted bit, not a finite-key security proof.
- Local, reproducible simulations using a fixed random seed.
- Browser UI using Pyodide to execute the same Python BB84 module, with optional JSON export.
- Separate generic audit API and CLI operations for demonstration, including a per-process HMAC-SHA256 chained audit log.

## Browser application

The `index.html` entry point runs on GitHub Pages or any static HTTP server. Select the qubit count, channel noise, seed and optional intercept-and-resend attack, then run the simulation. The first run downloads a pinned Pyodide runtime from a CDN. All BB84 computation is performed locally in the browser; no input or results are sent to the application server. Exported JSON contains the simulation trace and should not be treated as secret material.

GitHub Pages builds and publishes the `index.html`, `web/app.js` and `qkd_bb84_engine/engine.py` files using the deployment workflow. Pages must be configured to permit GitHub Actions deployments.

## Python installation

Requires Python 3.9 or newer.

```bash
git clone https://github.com/abusuraihsakhri/quantum-key-distribution-bb84.git
cd quantum-key-distribution-bb84
python -m pip install -e .
quantum-key-distribution-bb84 run --qubits 1000 --seed 42
python cli.py run --qubits 1000 --noise 0.04 --eavesdrop
python cli.py eavesdrop --qubits 500 --trials 10
python cli.py stats --qubits 500 --trials 25
python cli.py rate --qubits 1000 --qber 0.05
```

`--show-key` prints only educational outputs and should not be used in a real cryptographic context.

## Generic audit API (separate from the BB84 simulator)

The FastAPI endpoints operate a deterministic three-rule supervisory demo. The metrics and thresholds are **example rules**, not BB84 or NIST conformance assessments. Its mock chat implementation does not query a real language model.

```bash
python -m pip install -e '.[server]'
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py serve --host 127.0.0.1 --port 8000
```

- `GET /health`: service health
- `GET /metrics`: basic process-local counters as JSON
- `POST /api/audit`: generic rule-based evaluation and HMAC audit entry
- `GET /api/audit/logs`: process-local audit trail
- `POST /api/chat`: deterministic mock response

The `AUDIT_SECRET_KEY` environment variable must be at least 16 characters. The audit trail is stored **in memory only** and is lost upon restart. Signatures detect modification of logged fields, but do not provide external persistence or independent attestation. Regex-based identifier screening is limited and **does not establish HIPAA compliance**.

For the Docker deployment, set `AUDIT_SECRET_KEY` explicitly and run `docker compose up --build`. The default compose binding is `127.0.0.1:8000`; add authentication and TLS before exposing any API publicly.

## Testing

```bash
python -m pip install -e '.[server,test]'
export AUDIT_SECRET_KEY=test-audit-key-for-development-only-2026
python -m pytest -q
node --check web/app.js
```

GitHub Actions runs the tests on Python 3.10–3.13 and publishes the static browser app on updates to `master`. Desktop and mobile browsers capable of running WebAssembly and fetching the Pyodide CDN are required for the browser experience. No external Python packages are needed by the BB84 numerical engine.

## License

MIT. See [LICENSE](LICENSE).
