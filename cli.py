"""
CLI for BB84 Quantum Key Distribution Engine.
Provides commands for QKD simulation, eavesdropping analysis, and statistics.
"""
import argparse
import sys

from qkd_bb84_engine.engine import (
    bb84_protocol, eavesdrop_analysis, protocol_statistics,
    calculate_key_rate, binary_entropy, privacy_amplification,
)
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger, PHIGuard, SecurityException


def cmd_run(args):
    """Run a single BB84 protocol instance."""
    result = bb84_protocol(
        n_qubits=args.qubits,
        noise_prob=args.noise,
        eavesdrop=args.eavesdrop,
        seed=args.seed,
    )
    
    print(f"BB84 Quantum Key Distribution:")
    print(f"  Qubits transmitted:    {result['n_qubits']}")
    print(f"  Matching bases:        {result['matching_bases']} ({100*result['matching_bases']/result['n_qubits']:.1f}%)")
    print(f"  Sifted key length:     {result['sifted_key_length']}")
    print(f"  Sample size:           {result['sample_size']}")
    print(f"  Errors found:          {result['errors_found']}")
    print(f"  QBER:                  {result['qber']:.4f} ({100*result['qber']:.2f}%)")
    print(f"  Eavesdrop detected:    {result['eavesdrop_detected']}")
    print(f"  Final key length:      {result['final_key_length']}")
    print(f"  Keys match:            {result['keys_match']}")
    print(f"  Eve present:           {result['eavesdrop']}")
    print(f"  Channel noise:         {result['noise_prob']}")
    
    if args.show_key and result['final_key_length'] > 0:
        alice_key = ''.join(str(b) for b in result['final_key_alice'])
        bob_key = ''.join(str(b) for b in result['final_key_bob'])
        print(f"\n  Alice's key: {alice_key}")
        print(f"  Bob's key:   {bob_key}")
    
    if args.show_sifted and result['sifted_key_length'] > 0:
        sifted_a = ''.join(str(b) for b in result['sifted_alice'][:50])
        sifted_b = ''.join(str(b) for b in result['sifted_bob'][:50])
        print(f"\n  Sifted (Alice, first 50): {sifted_a}")
        print(f"  Sifted (Bob, first 50):   {sifted_b}")
    
    return 0


def cmd_eavesdrop(args):
    """Analyze eavesdropping detection."""
    result = eavesdrop_analysis(
        n_qubits=args.qubits,
        n_trials=args.trials,
        seed=args.seed,
    )
    
    print(f"Eavesdropping Analysis ({result['n_trials']} trials, {result['n_qubits']} qubits each):")
    print(f"  Avg QBER (no Eve):     {result['avg_qber_no_eavesdrop']:.4f}")
    print(f"  Avg QBER (with Eve):   {result['avg_qber_with_eavesdrop']:.4f}")
    print(f"  Detection threshold:   {result['eavesdrop_threshold']}")
    print(f"  Eve detected:          {result['eve_detected']}")
    print(f"  Distinguishable:       {result['distinguishable']}")
    return 0


def cmd_stats(args):
    """Gather protocol statistics."""
    result = protocol_statistics(
        n_qubits=args.qubits,
        n_trials=args.trials,
        seed=args.seed,
    )
    
    print(f"BB84 Protocol Statistics ({result['n_trials']} trials):")
    print(f"  Avg sifted key length: {result['avg_sifted_length']:.1f}")
    print(f"  Theoretical fraction:  {result['theoretical_sifted_fraction']:.2f}")
    print(f"  Avg QBER:              {result['avg_qber']:.4f}")
    print(f"  Avg final key length:  {result['avg_key_length']:.1f}")
    print(f"  False alarm rate:      {result['false_alarm_rate']:.4f}")
    return 0


def cmd_rate(args):
    """Calculate key generation rate."""
    rate = calculate_key_rate(args.qubits, args.qber)
    h = binary_entropy(args.qber)
    print(f"Key Rate Analysis:")
    print(f"  QBER:                  {args.qber:.4f}")
    print(f"  Binary entropy H(e):   {h:.4f}")
    print(f"  Key rate:              {rate:.4f}")
    print(f"  Usable:                {rate > 0}")
    return 0


def cmd_audit(args):
    """Run a supervisor audit task."""
    from agents.models import SystemTaskPayload
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id=args.task_id,
        target_identifier=args.target_id,
        primary_metric=args.primary_metric,
        secondary_metric=args.secondary_metric,
        status_descriptor=args.status_descriptor,
        is_critical_flag=args.is_critical_flag,
    )
    dossier = supervisor.process_task(payload)
    print(f"Audit Dossier Generated:")
    print(f"  Dossier ID:        {dossier.dossier_id}")
    print(f"  Task ID:           {dossier.task_id}")
    print(f"  Overall Urgency:   {dossier.overall_urgency.value}")
    print(f"  Integrity Status:  {dossier.integrity_status.value}")
    print(f"  Total Alerts:      {dossier.total_alerts}")
    print(f"  Audit Hash:        {dossier.audit_hash}")
    return 0


def cmd_chat(args):
    """Query the supervisory chat system."""
    supervisor = SystemSupervisor(model_provider="mock")
    query = " ".join(args.query)
    try:
        response = supervisor.query_supervisory_chat(query)
        print(f"Supervisory Response:")
        print(f"  {response}")
    except SecurityException as e:
        print(f"Security violation: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_verify_audit(args=None):
    """Verify the integrity of the audit trail."""
    verified = AuditLogger.verify_integrity()
    trail_len = len(AuditLogger.get_trail())
    print(f"Audit Trail Verification:")
    print(f"  Blocks:    {trail_len}")
    print(f"  Integrity: {'VERIFIED' if verified else 'COMPROMISED'}")
    return 0 if verified else 1


def cmd_serve(args):
    """Start the FastAPI web server."""
    try:
        import uvicorn
        from agents.api import app
        print(f"Starting Quantum Key Distribution BB84 API server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    except ImportError:
        print("Error: uvicorn is required to run the server. Install with: pip install uvicorn", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="quantum-key-distribution-bb84",
        description="BB84 Quantum Key Distribution — real QKD simulation"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p = sub.add_parser("run", help="Run BB84 protocol")
    p.add_argument("-n", "--qubits", type=int, default=100, help="Number of qubits")
    p.add_argument("--noise", type=float, default=0.0, help="Channel noise probability")
    p.add_argument("--eavesdrop", action="store_true", help="Enable eavesdropping")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument("--show-key", action="store_true", help="Show final keys")
    p.add_argument("--show-sifted", action="store_true", help="Show sifted keys")

    # eavesdrop
    p = sub.add_parser("eavesdrop", help="Analyze eavesdropping detection")
    p.add_argument("-n", "--qubits", type=int, default=500, help="Qubits per trial")
    p.add_argument("--trials", type=int, default=10, help="Number of trials")
    p.add_argument("--seed", type=int, default=42, help="Random seed")

    # stats
    p = sub.add_parser("stats", help="Protocol statistics")
    p.add_argument("-n", "--qubits", type=int, default=200, help="Qubits per trial")
    p.add_argument("--trials", type=int, default=50, help="Number of trials")
    p.add_argument("--seed", type=int, default=42, help="Random seed")

    # rate
    p = sub.add_parser("rate", help="Key rate calculation")
    p.add_argument("-n", "--qubits", type=int, default=1000, help="Number of qubits")
    p.add_argument("--qber", type=float, default=0.05, help="Quantum bit error rate")

    # audit
    p = sub.add_parser("audit", help="Run supervisor audit task")
    p.add_argument("--task-id", default="TASK-CLI-001", help="Task identifier")
    p.add_argument("--target-id", default="TARGET-001", help="Target identifier")
    p.add_argument("--primary-metric", type=float, default=10.0, help="Primary metric value")
    p.add_argument("--secondary-metric", type=float, default=5.0, help="Secondary metric value")
    p.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    p.add_argument("--is-critical-flag", action="store_true", help="Critical flag")

    # chat
    p = sub.add_parser("chat", help="Query supervisory chat system")
    p.add_argument("query", nargs="+", help="Query text")

    # verify-audit
    p = sub.add_parser("verify-audit", help="Verify audit trail integrity")

    # serve
    p = sub.add_parser("serve", help="Start FastAPI web server")
    p.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    p.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args(argv)
    handlers = {
        'run': cmd_run,
        'eavesdrop': cmd_eavesdrop,
        'stats': cmd_stats,
        'rate': cmd_rate,
        'audit': cmd_audit,
        'chat': cmd_chat,
        'verify-audit': cmd_verify_audit,
        'serve': cmd_serve,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
