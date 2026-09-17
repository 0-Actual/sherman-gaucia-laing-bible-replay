"""Tests for the NEW adapter. No historical hash tests run here."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest

import replay

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
            self.assertTrue(all(check["passed"] for row in [result["baseline"], *result["studies"]] for check in row["checks"]))
            for name in ("results.json", "index.html", "REPLAY_REPORT.md"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_markdown_html_is_escaped(self):
        rendered = replay.render_markdown('<script src="https://invalid.test/x.js"></script>\n\n**Let there be light:**')
        self.assertNotIn("<script", rendered)
        self.assertIn("&lt;script", rendered)
        self.assertIn("<strong>Let there be light:</strong>", rendered)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, default=ENGINE)
    parser.add_argument("--studies", type=Path, default=STUDIES)
    args, remainder = parser.parse_known_args()
    ENGINE, STUDIES = args.engine, args.studies
    unittest.main(argv=[__file__, *remainder])
