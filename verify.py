#!/usr/bin/env python3
"""New 2026-09-17 integration: replay studies and run the selected offline tests."""
from __future__ import annotations

import importlib.util
import json
import os
import uuid

import replay
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



def complete_suite_passed(result, required_count: int) -> bool:
    return (result.wasSuccessful() and result.testsRun == required_count and not result.skipped
            and not result.expectedFailures and not result.unexpectedSuccesses)


def main() -> int:
    try:
        with replay.output_lock(ROOT / "verification"):
            return _verify()
    except (OSError, replay.ReplayError) as error:
        print(f"Verification could not start: {error}. No new verification is established.", file=sys.stderr)
        return 2

def _verify() -> int:
    """Write a truthful current attempt on every controlled exit.

    Verification is bound to the replay attempt checked, not an inherited file.
    A sibling attempt record survives replay's output-directory replacement.
    """
    output = ROOT / "replay-output"
    destination = output / "verification.json"
    attempt_path = ROOT / ".verification-attempt.json"
    report = {
        "integration_authored_date": "2026-09-17", "repaired_date": "2026-09-20",
        "verification_attempt_id": uuid.uuid4().hex, "state": "INCOMPLETE",
        "scope": "Study replay and adapter tests, plus 40 recovered WORD_CORE tests",
        "results": {}, "legacy_forensic_verifier_executed": False,
        "owner_signature": None, "new_fingerprints_generated": False,
        "replay_attempt_id": None,
    }
    outcomes = report["results"]

    def record():
        replay.atomic_json(attempt_path, report)
        output.mkdir(parents=True, exist_ok=True)
        replay.atomic_json(destination, report)

    try:
        # Invalidate old verification before executing any new check.
        record()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for name in ("replay.py", "test_replay.py"):
            completed = subprocess.run([sys.executable, str(ROOT / name)], cwd=ROOT,
                                       env=environment, check=False)
            outcomes[name] = {"exit_code": completed.returncode}
            if completed.returncode:
                report.update(state="FAIL", failed_step=name)
                record()
                print(f"Verification stopped: {name} returned {completed.returncode}.", file=sys.stderr)
                return 1
            if name == "replay.py":
                run = json.loads((output / "run-status.json").read_text(encoding="utf-8"))
                result = json.loads((output / "results.json").read_text(encoding="utf-8"))
                if run.get("state") != "COMPLETE" or run.get("status") != "PASS" or result.get("status") != "PASS":
                    raise replay.ReplayError("Replay returned success without complete passing artifacts")
                report["replay_attempt_id"] = run["attempt_id"]
                record()

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
            "passed": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
                      - len(result.expectedFailures) - len(result.unexpectedSuccesses),
            "failures": len(result.failures), "errors": len(result.errors),
            "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses),
            "excluded_archival_tests": sorted(ARCHIVAL_TESTS),
            "selection_reason": "Preserve historical witnesses without generating new fingerprints",
        }
        with replay.output_lock(output):
            run = json.loads((output / "run-status.json").read_text(encoding="utf-8"))
            if run.get("attempt_id") != report["replay_attempt_id"] or run.get("state") != "COMPLETE" or run.get("status") != "PASS":
                raise replay.ReplayError("Replay generation changed during verification; integration is incomplete")
            success = complete_suite_passed(result, 40)
            report["state"] = "PASS" if success else "FAIL"
            record()
        print(f"Verification: {report['state']}. Results: replay-output/verification.json")
        return 0 if success else 1
    except Exception as error:
        report.update(state="ERROR", error_type=type(error).__name__, error=str(error))
        try:
            record()
        except OSError as record_error:
            print(f"Cannot persist current verification failure: {record_error}. No current verification is established.", file=sys.stderr)
        print(f"Verification failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
