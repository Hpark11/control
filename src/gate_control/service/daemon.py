from __future__ import annotations

from gate_control.client.session import GateClientSession


def run_daemon(session: GateClientSession) -> None:
    print("Daemon started. Press Ctrl+C to stop.")
    try:
        session.monitor()
    except KeyboardInterrupt:
        print("Stopping daemon...")
    finally:
        session.close()
