"""
# ============================================================
# Context Banner — test_testqueue | Category: test
# Purpose: Verifiziert queued Test Runner (submit/status/list) via admin_devtools.

# Contracts
#   - submit_test_run gibt run_id (str)
#   - list_test_runs zeigt queued/running/finished Einträge
#   - get_test_run liefert Status-Dict mit Pflichtfeldern

# Invariants
#   - Kein paralleler Thread erforderlich (process tick implicit)
#   - Invalid Filter führt zu 0 Tests aber status passed|failed (kein crash)

# Dependencies
#   Internal: app.ui.admin_devtools (queue API)
#   External: stdlib

# Do-Not-Change
#   Banner policy-relevant
# ============================================================
"""
from app.ui import admin_devtools as adm_dt


def test_testqueue_basic_flow():
    run_id = adm_dt.submit_test_run(k_expr="metrics")
    assert isinstance(run_id, str) and len(run_id) >= 6
    # First listing should process & finish (single run) synchron synchronously
    rows = adm_dt.list_test_runs(limit=5)
    assert any(r["run_id"] == run_id for r in rows)
    # Get status
    st = adm_dt.get_test_run(run_id)
    assert st["status"] in {"passed","failed"}
    assert "stdout" in st


def test_testqueue_invalid_filter():
    run_id = adm_dt.submit_test_run(k_expr="__no_such_test__")
    adm_dt.process_test_queue()
    st = adm_dt.get_test_run(run_id)
    assert st["status"] in {"passed","failed"}  # empty selection may still be passed
    # counts 0 allowed
    assert st["passed"] >= 0
    assert st["failed"] >= 0
