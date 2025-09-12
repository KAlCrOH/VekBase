"""
# ============================================================
# Context Banner — test_devtools | Category: test
# Purpose: Verifiziert DevTools Discovery & Run Wrapper (happy path + Negativfall)

# Contracts
#   Inputs: Filter / NodeIDs
#   Outputs: Assertions auf Ergebnisstatus / stdout Struktur
#   Side-Effects: Startet subprocess pytest (nested) – akzeptabel im kleinen Projektumfang
#   Determinism: Deterministisch für stabile Testbasis

# Invariants
#   - Discovery darf bei 0 Treffern keine Exception werfen
#   - run_tests mit ungültigem NodeID -> status failed

# Dependencies
#   Internal: app.core.devtools
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.core import devtools


def test_discover_and_run_subset():
    nodeids = devtools.discover_tests(k_expr="metrics", module_substr="test_metrics")
    # Should collect at least one test from test_metrics
    assert any("test_metrics.py::" in n for n in nodeids)
    # Run only first test to keep runtime low
    subset = nodeids[:1]
    res = devtools.run_tests(nodeids=subset)
    assert res.status in ("passed",)  # single test should pass
    # In -q mode a single passing test may render only '.'; ensure stdout not empty
    assert res.stdout.strip() != ""


def test_run_invalid_nodeid_failure():
    res = devtools.run_tests(nodeids=["tests/test_nonexistent_module.py::test_nowhere"])
    # Pytest should fail (collection error) -> status failed
    assert res.status == "failed"
    assert res.returncode != 0
    # stdout or stderr should mention not found
    assert "ERROR" in (res.stdout + res.stderr) or "not found" in (res.stdout + res.stderr).lower()
