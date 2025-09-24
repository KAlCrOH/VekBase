#!/usr/bin/env python
"""Sequential test batch runner to optimize resource usage.
Usage:
  python scripts/run_test_batches.py [--maxfail 1]
Environment Vars:
  VEK_TEST_MAXFAIL: overrides --maxfail argument if set.
  VEK_TEST_LOCK_TIMEOUT: seconds to wait for existing test lock (default 30).

Batches chosen to front-load core & fast tests, then heavier ones.
"""
from __future__ import annotations
import subprocess, sys, argparse, shutil

BATCHES = [
    ["pytest", "tests/test_decision_card*.py", "tests/test_trade_model.py", "tests/test_retrieval.py", "-q"],
    ["pytest", "-k", "analytics_ext or metrics or rolling_volatility", "-q"],
    ["pytest", "tests/test_admin_devtools.py", "tests/test_devtools*.py", "-q"],
    ["pytest", "-k", "strategy_batch or simulation or sim_persist", "-q"],
    ["pytest", "-q"],  # catch-all final
]

def run_batch(cmd: list[str], maxfail: int | None) -> int:
    full = list(cmd)
    if maxfail:
        full.extend(["--maxfail", str(maxfail)])
    print(f"\n=== Running: {' '.join(full)} ===", flush=True)
    proc = subprocess.run(full)
    return proc.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maxfail', type=int, default=None)
    args = ap.parse_args()
    # env override
    import os
    mf_env = os.environ.get('VEK_TEST_MAXFAIL')
    if mf_env:
        try:
            args.maxfail = int(mf_env)
        except ValueError:
            pass
    for i, batch in enumerate(BATCHES, start=1):
        rc = run_batch(batch, args.maxfail)
        if rc != 0:
            print(f"Stopping after batch {i} (exit code {rc}).", flush=True)
            sys.exit(rc)
    print("All batches passed.")

if __name__ == '__main__':
    main()
