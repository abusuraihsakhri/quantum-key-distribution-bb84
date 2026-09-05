"""
Pytest configuration for quantum-key-distribution-bb84 tests.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a test audit secret key if not already set
if not os.getenv("AUDIT_SECRET_KEY"):
    os.environ["AUDIT_SECRET_KEY"] = "test-audit-key-for-development-only-2026"
