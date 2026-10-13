"""Regression tests for QKD safety, signature verification and packaging."""
import random
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail
from qkd_bb84_engine.engine import (
    bb84_protocol, privacy_amplification, calculate_key_rate,
)


def test_zero_qber_yields_idealized_full_asymptotic_fraction():
    assert calculate_key_rate(1000, 0.0) == 1.0
    assert calculate_key_rate(1000, 0.11) < 0.01


def test_long_amplifier_output_does_not_append_constant_zeroes():
    input_bits = [i % 2 for i in range(1024)]
    result = privacy_amplification(input_bits, output_length=512)
    assert len(result) == 512
    assert any(result[i] for i in range(256, 512))
    with pytest.raises(ValueError):
        privacy_amplification(input_bits, output_length=1025)


def test_insufficient_samples_do_not_produce_keys():
    result = bb84_protocol(1, seed=4)
    assert result["aborted"]
    assert result["final_key_length"] == 0
    assert not result["parameter_estimation_possible"]
    assert not result["keys_match"]


def test_uncorrected_bit_errors_abort_key_generation():
    result = bb84_protocol(1000, noise_prob=0.08, seed=17)
    assert result["aborted"]
    assert result["final_key_length"] == 0
    assert not result["keys_match"]


def test_seeded_run_does_not_change_global_rng():
    random.seed(91)
    before = random.getstate()
    first = bb84_protocol(100, seed=42)
    second = bb84_protocol(100, seed=42)
    assert random.getstate() == before
    assert first == second


def test_chained_audit_rejects_modified_fields_and_hmac():
    trail = AuditTrail("development-test-key-123456789")
    trail.log("actor", "role", "first", {"metric": 12})
    trail.log("actor", "role", "second", {"metric": 15})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "changed"
    assert not trail.verify_integrity()
    trail.logs[0]["event_type"] = "first"
    assert trail.verify_integrity()
    trail.logs[1]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_public_copy_cannot_mutate_in_memory_audit():
    trail = AuditTrail("development-test-key-123456789")
    trail.log("actor", "role", "event", {})
    trail.get_trail()[0]["actor"] = "other"
    assert trail.verify_integrity()


def test_http_validates_parameters_and_handles_sensitive_ids():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    payload = {
        "task_id": "T-1", "target_identifier": "KEY-01",
        "primary_metric": 3.0, "secondary_metric": 1.0
    }
    assert client.post("/api/audit", json=payload).status_code == 200
    assert client.post("/api/audit", json={**payload, "primary_metric": "NaN"}).status_code == 422
    sensitive = {**payload, "target_identifier": "MRN-123456"}
    assert client.post("/api/audit", json=sensitive).status_code == 422


def test_package_entrypoint_uses_supported_cli():
    matches = [entry for entry in entry_points(group="console_scripts")
               if entry.name == "quantum-key-distribution-bb84"]
    assert matches
    assert matches[0].value == "cli:main"
    from qkd_bb84_engine.cli import main as legacy_main
    assert legacy_main(["chat", "status"]) == 0


def test_pages_entrypoint_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "index.html").is_file()
    assert (root / "web" / "app.js").is_file()
