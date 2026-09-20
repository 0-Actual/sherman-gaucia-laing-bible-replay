"""Tests for the NEW adapter. No historical hash tests run here."""
from __future__ import annotations

import argparse
import copy
import json
import io
import os
import shutil
import subprocess
import sys
from unittest import mock
from pathlib import Path
import tempfile
import unicodedata
import unittest

import replay
import verify

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "original" / "word_core" / "qel_word_core_reference_v2.py"
STUDIES = HERE / "studies"

# Independent expectations copied from the recovered saved study tables,
# not calculated using the code under test.
KNOWN_VERSES = {
    1: (2701, 7, 28, 373),
    2: (3546, 14, 52, 576),
    3: (813, 6, 23, 1500),
    4: (1776, 12, 45, 171),
    5: (2141, 13, 49, 154),
}
KNOWN_LESSON_COUNTS = [10772, 10709, 10392, 10281, 10192]


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = replay.load_engine(ENGINE)
        cls.documents = [json.loads((STUDIES / f"Genesis_1_{v}_Expanded_Study.json").read_text(encoding="utf-8"))
                         for v in range(1, 6)]

    def test_five_saved_verse_known_answers(self):
        for verse, doc in enumerate(self.documents, 1):
            with self.subTest(verse=verse):
                calc = doc["text_and_calculations"]
                standard = replay.hebrew_lanes(calc["hebrew_pointed"], "test", self.engine)["standard"]
                greek = replay.greek_selected_word(calc["selected_greek_witness"]["word"], self.engine)
                self.assertEqual((standard["total"], standard["word_count"], standard["letter_count"], greek["total"]), KNOWN_VERSES[verse])

    def test_genesis_one_known_answer_all_four_schemes(self):
        # From the recovered QEL_WORD_CORE_REFERENCE_KAT_V2.json fixture.
        lanes = replay.hebrew_lanes("בראשית ברא אלהים את השמים ואת הארץ", "test", self.engine)
        self.assertEqual([lanes[s]["total"] for s in replay.SCHEMES], [2701, 4631, 298, 82])

    def test_final_letter_conventions(self):
        # Ordinary 20+40+50+80+90=280; Gadol 500+600+700+800+900=3500.
        lanes = replay.hebrew_lanes("ךםןףץ", "test", self.engine)
        # Ordinal 11+13+14+17+18=73; reduced 2+4+5+8+9=28.
        self.assertEqual([lanes[s]["total"] for s in replay.SCHEMES], [280, 3500, 73, 28])

    def test_maqaf_boundary_preserves_value(self):
        joined = replay.hebrew_lanes("עַל־פְּנֵי", "test", self.engine, "join")["standard"]
        split = replay.hebrew_lanes("עַל־פְּנֵי", "test", self.engine, "split")["standard"]
        self.assertEqual((joined["total"], split["total"]), (240, 240))
        self.assertEqual((joined["word_count"], split["word_count"]), (1, 2))

    def test_nfc_nfd_equivalence(self):
        raw = self.documents[0]["text_and_calculations"]["hebrew_pointed"]
        nfc = replay.hebrew_lanes(unicodedata.normalize("NFC", raw), "test", self.engine)
        nfd = replay.hebrew_lanes(unicodedata.normalize("NFD", raw), "test", self.engine)
        self.assertEqual(nfc, nfd)

    def test_hebrew_rejects_foreign_letters_numbers_symbols_controls(self):
        for raw in ("אa", "א1", "א🙂", "א\x00", "א\u200b", "א\u0301", ""):
            with self.subTest(raw=raw), self.assertRaises((replay.ReplayError, self.engine.WordCoreError)):
                replay.hebrew_lanes(raw, "test", self.engine)

    def test_punctuation_whitespace_and_marks(self):
        result = replay.hebrew_lanes("\tא, ב!\nג׃", "test", self.engine)["standard"]
        self.assertEqual((result["calculation_surface"], result["total"], result["word_count"]), ("א ב ג", 6, 3))

    def test_reject_empty_calculation_surface(self):
        with self.assertRaises(self.engine.WordCoreError):
            replay.hebrew_lanes("...", "test", self.engine)

    def test_greek_final_sigma_and_accents(self):
        self.assertEqual(replay.greek_selected_word("λόγος", self.engine)["total"], 373)
        self.assertEqual(replay.greek_selected_word("ΛΟΓΟΣ", self.engine)["total"], 373)
        self.assertEqual(replay.greek_selected_word("καλός", self.engine)["total"], 321)

    def test_greek_profile_is_explicitly_limited(self):
        for word in ("β", "logos", "λόγος🙂", "λόγος1", "λογος λογος", ""):
            with self.subTest(word=word), self.assertRaises(replay.ReplayError):
                replay.greek_selected_word(word, self.engine)

    def test_saved_wordcounts_and_exact_baseline_ratio(self):
        self.assertEqual([len(d["lesson_markdown"].split()) for d in self.documents], KNOWN_LESSON_COUNTS)
        baseline = json.loads((STUDIES / "QEL_Genesis_1_1_Study_20260910.json").read_text(encoding="utf-8"))
        self.assertEqual(len(baseline["lesson_markdown"].split()), 5386)
        self.assertEqual(KNOWN_LESSON_COUNTS[0], 2 * 5386)

    def test_incorrect_claimed_total_is_failure(self):
        doc = copy.deepcopy(self.documents[0])
        doc["text_and_calculations"]["total"] = 2702
        result = replay.study_replay(doc, doc["lesson_markdown"], "fixture.json", self.engine, 5386)
        self.assertEqual(result["state"], "FAIL")
        self.assertEqual([check["check"] for check in result["checks"] if not check["passed"]], ["standard_total"])

    def test_changed_saved_lesson_count_is_failure(self):
        doc = copy.deepcopy(self.documents[0])
        doc["lesson_markdown"] += " EXTRA"
        result = replay.study_replay(doc, doc["lesson_markdown"], "fixture.json", self.engine, 5386)
        self.assertEqual(result["state"], "FAIL")
        self.assertIn("saved_lesson_word_count", [check["check"] for check in result["checks"] if not check["passed"]])

    def test_replay_outputs_identical_on_repeated_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "first", Path(tmp) / "second"
            result = replay.replay(STUDIES, ENGINE, first)
            replay.replay(STUDIES, ENGINE, second)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(len(result["studies"]), 5)
            self.assertEqual(sum(len(row["checks"]) for row in [result["baseline"], *result["studies"]]), 113)
            self.assertTrue(all(check["passed"] for row in [result["baseline"], *result["studies"]] for check in row["checks"]))
            reader = (first / "index.html").read_text(encoding="utf-8")
            self.assertIn('Overall replay status: <strong>PASS</strong>', reader)
            self.assertIn('Required Genesis 1:1 baseline status: <strong>PASS</strong>', reader)
            self.assertIn('No failed source comparisons.', reader)
            for name in ("results.json", "index.html", "REPLAY_REPORT.md"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_markdown_html_is_escaped(self):
        rendered = replay.render_markdown('<script src="https://invalid.test/x.js"></script>\n\n**Let there be light:**')
        self.assertNotIn("<script", rendered)
        self.assertIn("&lt;script", rendered)
        self.assertIn("<strong>Let there be light:</strong>", rendered)

    def test_overview_reuses_only_exact_saved_verse_emphasis(self):
        doc = self.documents[2]
        verse = doc["text_and_calculations"]["kjv"]
        rendered = replay.render_saved_verse(verse, doc["lesson_markdown"])
        self.assertIn("<strong>Let there be light:</strong>", rendered)
        self.assertEqual(rendered.replace("<strong>", "").replace("</strong>", ""), verse)
        self.assertEqual(replay.render_saved_verse(verse, "**Let there be light:**"), verse)
        self.assertEqual(replay.render_saved_verse(verse, "> **Different words**"), verse)
        repeated = "> " + verse + "\n> " + verse
        self.assertEqual(replay.render_saved_verse(verse, repeated), verse)


class ReplayFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.studies = self.root / "studies"
        shutil.copytree(STUDIES, self.studies)
        self.output = self.root / "output"
        self.study = self.studies / "Genesis_1_1_Expanded_Study.json"

    def mutate(self, change):
        document = json.loads(self.study.read_text(encoding="utf-8"))
        change(document)
        self.study.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    def run_replay(self):
        return replay.replay(self.studies, ENGINE, self.output)

    def assert_incomplete(self):
        run = json.loads((self.output / "run-status.json").read_text(encoding="utf-8"))
        results = json.loads((self.output / "results.json").read_text(encoding="utf-8"))
        self.assertEqual((run["state"], run["status"]), ("INCOMPLETE", "ERROR"))
        self.assertEqual(results["status"], "ERROR")
        self.assertFalse((self.output / "index.html").exists())
        self.assertFalse((self.output / "REPLAY_REPORT.md").exists())
        self.assertNotEqual(json.loads((self.output / "verification.json").read_text(encoding="utf-8"))["state"], "PASS")

    def test_missing_greek_cannot_publish_fresh_pass(self):
        self.mutate(lambda d: d["text_and_calculations"].pop("selected_greek_witness"))
        with self.assertRaisesRegex(replay.ReplayError, "selected_greek_witness"):
            self.run_replay()
        self.assert_incomplete()

    def test_baseline_requires_greek_too(self):
        self.study = self.studies / "QEL_Genesis_1_1_Study_20260910.json"
        self.mutate(lambda d: d["word_core"].pop("selected_greek_witness"))
        with self.assertRaises(replay.ReplayError):
            self.run_replay()
        self.assert_incomplete()

    def test_baseline_comparison_failure_is_visible_in_reader(self):
        self.study = self.studies / "QEL_Genesis_1_1_Study_20260910.json"
        self.mutate(lambda d: d["word_core"].update(total=2702))
        result = self.run_replay()
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["baseline"]["state"], "FAIL")
        self.assertTrue(all(row["state"] == "PASS" for row in result["studies"]))
        reader = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn('Overall replay status: <strong>FAIL</strong>', reader)
        self.assertIn('Required Genesis 1:1 baseline status: <strong>FAIL</strong>', reader)
        self.assertIn('Baseline · Genesis 1:1', reader)
        self.assertIn('standard total: calculated 2701; saved expected 2702.', reader)
        self.assertNotIn('No failed source comparisons.', reader)

    def test_expanded_comparison_failure_is_visible_in_reader(self):
        self.mutate(lambda d: d["text_and_calculations"].update(total=2702))
        result = self.run_replay()
        self.assertEqual(result["status"], "FAIL")
        reader = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn('Overall replay status: <strong>FAIL</strong>', reader)
        self.assertIn('Required Genesis 1:1 baseline status: <strong>PASS</strong>', reader)
        self.assertIn('Expanded study · Genesis 1:1', reader)
        self.assertIn('standard total: calculated 2701; saved expected 2702.', reader)

    def test_top_level_and_nested_wrong_shapes_are_controlled(self):
        original = self.study.read_bytes()
        changes = [
            ("root_array", lambda d: []),
            ("validation_array", lambda d: {**d, "validation": []}),
            ("exposition_null", lambda d: {**d, "exposition": None}),
            ("calculation_array", lambda d: {**d, "text_and_calculations": []}),
            ("words_row", lambda d: {**d, "text_and_calculations": {**d["text_and_calculations"], "words": [None]}}),
            ("trace_row", lambda d: {**d, "text_and_calculations": {**d["text_and_calculations"],
                "selected_greek_witness": {**d["text_and_calculations"]["selected_greek_witness"], "trace": [None]}}}),
        ]
        for label, change in changes:
            with self.subTest(label=label):
                self.study.write_text(json.dumps(change(json.loads(original))), encoding="utf-8")
                with self.assertRaises(replay.ReplayError):
                    self.run_replay()
                self.assert_incomplete()

    def test_bool_numeric_and_duplicate_json_fields_rejected(self):
        self.mutate(lambda d: d["text_and_calculations"].update(total=True))
        with self.assertRaisesRegex(replay.ReplayError, "expected int"):
            self.run_replay()
        self.study.write_text('{"lesson_markdown":"a","lesson_markdown":"b"}', encoding="utf-8")
        with self.assertRaisesRegex(replay.ReplayError, "Duplicate JSON field"):
            self.run_replay()
        self.study.write_text('{"bad":NaN}', encoding="utf-8")
        with self.assertRaisesRegex(replay.ReplayError, "invalid JSON numeric constant"):
            self.run_replay()

    def test_required_clause_evidence_cannot_silently_reduce_comparisons(self):
        self.study = self.studies / "Genesis_1_3_Expanded_Study.json"
        self.mutate(lambda d: d["text_and_calculations"].pop("clause_subtotals"))
        with self.assertRaisesRegex(replay.ReplayError, "clause_subtotals"):
            self.run_replay()
        self.assert_incomplete()

    def test_failed_rerun_preserves_old_generation_but_invalidates_current(self):
        self.run_replay()
        old = (self.output / "results.json").read_bytes()
        replay.atomic_json(self.output / "verification.json", {"state": "PASS"})
        self.study.write_text("[]", encoding="utf-8")
        with self.assertRaises(replay.ReplayError):
            self.run_replay()
        self.assert_incomplete()
        previous = list(self.root.glob(".output.superseded-*"))
        self.assertEqual(len(previous), 1)
        self.assertEqual((previous[0] / "results.json").read_bytes(), old)

    def test_render_error_never_publishes_success_artifacts(self):
        with mock.patch.object(replay, "render_index", side_effect=RuntimeError("render fixture")):
            with self.assertRaisesRegex(replay.ReplayError, "render fixture"):
                self.run_replay()
        self.assert_incomplete()

    def test_staging_write_error_does_not_publish_partial_pass(self):
        real_write = Path.write_text
        def write(path, *args, **kwargs):
            if ".staging-" in str(path) and path.name == "index.html":
                raise OSError("write fixture")
            return real_write(path, *args, **kwargs)
        with mock.patch.object(Path, "write_text", write):
            with self.assertRaisesRegex(replay.ReplayError, "write fixture"):
                self.run_replay()
        self.assert_incomplete()

    def test_promotion_failure_restores_incomplete_current_generation(self):
        rename = Path.rename
        def fail_stage(path, target):
            if path.name.startswith(".output.staging-"):
                raise OSError("promotion fixture")
            return rename(path, target)
        with mock.patch.object(Path, "rename", fail_stage):
            with self.assertRaisesRegex(replay.ReplayError, "promotion fixture"):
                self.run_replay()
        self.assert_incomplete()

    def test_replay_only_invalidates_previous_integration_pass(self):
        self.run_replay()
        replay.atomic_json(self.output / "verification.json", {"state": "PASS"})
        self.run_replay()
        self.assertEqual(json.loads((self.output / "verification.json").read_text(encoding="utf-8"))["state"], "NOT_RUN")

    def test_output_must_not_overlap_source(self):
        before = self.study.read_bytes()
        for output in (self.studies, self.root, self.studies / "generated"):
            with self.subTest(output=output), self.assertRaises(replay.ReplayError):
                replay.replay(self.studies, ENGINE, output)
        self.assertEqual(self.study.read_bytes(), before)

    def test_lock_prevents_concurrent_writer_without_invalidating_active_output(self):
        self.run_replay()
        before = (self.output / "results.json").read_bytes()
        with replay.output_lock(self.output), self.assertRaisesRegex(replay.ReplayError, "locked"):
            self.run_replay()
        self.assertEqual((self.output / "results.json").read_bytes(), before)

    def test_cli_exit_codes_distinguish_comparison_failure_from_invalid_input(self):
        command = [sys.executable, str(HERE / "replay.py"), "--studies", str(self.studies),
                   "--engine", str(ENGINE), "--output", str(self.output)]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.mutate(lambda d: d["text_and_calculations"].update(total=2702))
        failed = subprocess.run(command, capture_output=True, text=True, env=environment)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        self.assertEqual(json.loads((self.output / "results.json").read_text(encoding="utf-8"))["status"], "FAIL")
        self.study.write_text("[]", encoding="utf-8")
        malformed = subprocess.run(command, capture_output=True, text=True, env=environment)
        self.assertEqual(malformed.returncode, 2, malformed.stderr)
        self.assertNotIn("Traceback", malformed.stderr)
        self.assert_incomplete()


class VerificationFailureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "replay-output").mkdir()
        self.destination = self.root / "replay-output" / "verification.json"
        replay.atomic_json(self.destination, {"state": "PASS", "stale": True})

    def test_replay_failure_replaces_old_verification_pass(self):
        with mock.patch.object(verify, "ROOT", self.root), mock.patch.object(verify.subprocess, "run", return_value=subprocess.CompletedProcess([], 2)):
            code = verify.main()
        current = json.loads(self.destination.read_text(encoding="utf-8"))
        self.assertEqual((code, current["state"], current["failed_step"]), (1, "FAIL", "replay.py"))
        self.assertNotIn("stale", current)

    def test_adapter_failure_replaces_old_verification_pass(self):
        def process(command, **kwargs):
            if command[1].endswith("replay.py") and not command[1].endswith("test_replay.py"):
                replay.atomic_json(self.root / "replay-output/run-status.json", {"state": "COMPLETE", "status": "PASS", "attempt_id": "fixture"})
                replay.atomic_json(self.root / "replay-output/results.json", {"status": "PASS"})
                return subprocess.CompletedProcess(command, 0)
            return subprocess.CompletedProcess(command, 1)
        with mock.patch.object(verify, "ROOT", self.root), mock.patch.object(verify.subprocess, "run", side_effect=process):
            code = verify.main()
        current = json.loads(self.destination.read_text(encoding="utf-8"))
        self.assertEqual((code, current["state"], current["failed_step"]), (1, "FAIL", "test_replay.py"))
        self.assertEqual(current["replay_attempt_id"], "fixture")

    def test_skipped_recovered_test_is_not_counted_as_pass(self):
        class Skipped(unittest.TestCase):
            @unittest.skip("fixture")
            def runTest(self):
                pass
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None) for _ in range(39)] + [Skipped()])
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        self.assertTrue(result.wasSuccessful())
        self.assertFalse(verify.complete_suite_passed(result, 40))

    def test_concurrent_verifier_cannot_overwrite_active_record(self):
        before = self.destination.read_bytes()
        with mock.patch.object(verify, "ROOT", self.root), replay.output_lock(self.root / "verification"):
            code = verify.main()
        self.assertEqual(code, 2)
        self.assertEqual(self.destination.read_bytes(), before)

    def test_launch_error_records_error_not_old_pass(self):
        with mock.patch.object(verify, "ROOT", self.root), mock.patch.object(verify.subprocess, "run", side_effect=OSError("launch fixture")):
            code = verify.main()
        current = json.loads(self.destination.read_text(encoding="utf-8"))
        self.assertEqual((code, current["state"]), (2, "ERROR"))
        self.assertIn("launch fixture", current["error"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, default=ENGINE)
    parser.add_argument("--studies", type=Path, default=STUDIES)
    args, remainder = parser.parse_known_args()
    ENGINE, STUDIES = args.engine, args.studies
    unittest.main(argv=[__file__, *remainder])
