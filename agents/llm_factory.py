"""
Deterministic mock responses with basic identifier screening; external LLM providers are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Quantum Key Distribution Bb84"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock mode]: No language-model analysis was performed. Query received: '{prompt[:60]}...'. Use the BB84 simulator for quantitative results."


class LLMFactory:
    """Selects a supported deterministic mock model."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Quantum Key Distribution Bb84"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError("Only deterministic mock mode is implemented")
