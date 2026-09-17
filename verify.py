#!/usr/bin/env python3
"""New 2026-09-17 integration: replay studies and run the selected offline tests."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent
ARCHIVAL_TESTS = {
    "test_034_surface_hash_matches_legacy_witness",
    "test_038_genesis_1_2_source_witness",
    "test_041_genesis_1_7_source_witness",
}


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main() -> int:
    outcomes = {}
    for name in ("replay.py", "test_replay.py"):
        completed = subprocess.run([sys.executable, str(ROOT / name)], cwd=ROOT, check=False)
        outcomes[name] = {"exit_code": completed.returncode}
        if completed.returncode:
            print(f"Verification stopped: {name} returned {completed.returncode}.", file=sys.stderr)
            return 1

    source_dir = ROOT / "original" / "word_core"
    sys.path.insert(0, str(source_dir))
    spec = importlib.util.spec_from_file_location(
        "qel_recovered_tests", source_dir / "test_qel_word_core_reference_v2.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load recovered WORD_CORE tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    recovered = list(flatten(unittest.defaultTestLoader.loadTestsFromModule(module)))
    names = {test._testMethodName for test in recovered}
    if len(recovered) != 43 or not ARCHIVAL_TESTS.issubset(names):
        raise RuntimeError("Recovered test inventory changed; review the selection before running")
    selected = [test for test in recovered if test._testMethodName not in ARCHIVAL_TESTS]
    result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(selected))
    outcomes["recovered_word_core"] = {
        "executed": result.testsRun,
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "excluded_archival_tests": sorted(ARCHIVAL_TESTS),
        "selection_reason": "Preserve historical witnesses without generating new fingerprints",
    }
    success = result.wasSuccessful()
    report = {
        "integration_authored_date": "2026-09-17",
        "state": "PASS" if success else "FAIL",
        "scope": "New study replay and adapter tests, plus 40 recovered WORD_CORE tests",
        "results": outcomes,
        "legacy_forensic_verifier_executed": False,
        "owner_signature": None,
        "new_fingerprints_generated": False,
    }
    destination = ROOT / "replay-output" / "verification.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verification: {report['state']}. Results: replay-output/verification.json")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
