from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unicodedata
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from qel_word_core_reference_v2 import (  # noqa: E402
    IdentityBundle,
    WordCoreError,
    calculate_hebrew,
    calculate_named_hebrew_lanes,
    digital_root,
    transform_greek,
    transform_hebrew,
)

SOURCE_ID = "Genesis-1-1-governing-calc-surface/e6eff815"
TRANSFORM_ID = "QEL-WORD-CORE-HEBREW-TRANSFORM-REFERENCE-v2"
PROFILE_ID = "qel_gematria_core_profile_v1/04b534a9"
POINTED_GEN_1_1 = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
CONSONANTAL_GEN_1_1 = "בראשית ברא אלהים את השמים ואת הארץ"


def ids(scheme: str, *, source: str = SOURCE_ID, transform: str = TRANSFORM_ID, profile: str = PROFILE_ID):
    return IdentityBundle(source, transform, profile, "hebrew", scheme)


class WordCoreReferenceTests(unittest.TestCase):
    def test_001_pointed_to_governing_surface(self):
        self.assertEqual(transform_hebrew(POINTED_GEN_1_1, maqaf_mode="join"), CONSONANTAL_GEN_1_1)

    def test_002_nfc_nfd_equivalence(self):
        nfc = unicodedata.normalize("NFC", POINTED_GEN_1_1)
        nfd = unicodedata.normalize("NFD", POINTED_GEN_1_1)
        self.assertEqual(transform_hebrew(nfc, maqaf_mode="join"), transform_hebrew(nfd, maqaf_mode="join"))

    def test_003_genesis_standard_total(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))
        self.assertEqual((r["word_count"], r["letter_count"], r["total"], r["binary"]), (7, 28, 2701, "101010001101"))

    def test_004_genesis_gadol_total(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("gadol"))
        self.assertEqual(r["total"], 4631)

    def test_005_genesis_ordinal_total(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("ordinal"))
        self.assertEqual(r["total"], 298)

    def test_006_genesis_reduced_total(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("reduced"))
        self.assertEqual(r["total"], 82)

    def test_007_separate_named_lanes(self):
        lanes = calculate_named_hebrew_lanes(
            POINTED_GEN_1_1, source_id=SOURCE_ID, transform_id=TRANSFORM_ID, profile_id=PROFILE_ID
        )
        self.assertEqual(set(lanes), {"standard", "gadol", "ordinal", "reduced"})
        self.assertEqual([lanes[x]["total"] for x in ("standard", "gadol", "ordinal", "reduced")], [2701, 4631, 298, 82])

    def test_008_final_form_separation(self):
        self.assertEqual(calculate_hebrew("ךםןףץ", identities=ids("standard"))["total"], 280)
        self.assertEqual(calculate_hebrew("ךםןףץ", identities=ids("gadol"))["total"], 3500)

    def test_009_genesis_final_delta(self):
        std = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))["total"]
        gadol = calculate_hebrew(POINTED_GEN_1_1, identities=ids("gadol"))["total"]
        self.assertEqual(gadol - std, 1930)

    def test_010_vav_mutation(self):
        self.assertEqual(calculate_hebrew("ואת", identities=ids("standard"))["total"], 407)
        self.assertEqual(calculate_hebrew("את", identities=ids("standard"))["total"], 401)

    def test_011_maqaf_join_split_totals(self):
        raw = "עַל־פְּנֵי"
        joined = calculate_hebrew(raw, identities=ids("standard"), maqaf_mode="join")
        split = calculate_hebrew(raw, identities=ids("standard"), maqaf_mode="split")
        self.assertEqual(joined["total"], split["total"])
        self.assertEqual(joined["total"], 240)
        self.assertEqual((joined["word_count"], split["word_count"]), (1, 2))

    def test_012_maqaf_gadol_invariance(self):
        raw = "מִן־הָאָרֶץ"
        joined = calculate_hebrew(raw, identities=ids("gadol"), maqaf_mode="join")
        split = calculate_hebrew(raw, identities=ids("gadol"), maqaf_mode="split")
        self.assertEqual(joined["total"], split["total"])

    def test_013_binary_round_trip(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))
        self.assertEqual(r["binary_round_trip"], r["total"])

    def test_014_word_rows_sum_to_total(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))
        self.assertEqual(sum(row["subtotal"] for row in r["rows"]), r["total"])

    def test_015_letter_rows_match_surface(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))
        self.assertEqual(sum(len(row["letters"]) for row in r["rows"]), r["letter_count"])

    def test_016_known_word_values(self):
        r = calculate_hebrew(CONSONANTAL_GEN_1_1, identities=ids("standard"))
        self.assertEqual([row["subtotal"] for row in r["rows"]], [913, 203, 86, 401, 395, 407, 296])

    def test_017_known_gadol_words(self):
        r = calculate_hebrew(CONSONANTAL_GEN_1_1, identities=ids("gadol"))
        self.assertEqual([row["subtotal"] for row in r["rows"]], [913, 203, 646, 401, 955, 407, 1106])

    def test_018_missing_source_identity_rejected(self):
        with self.assertRaises(WordCoreError):
            calculate_hebrew("ברא", identities=ids("standard", source=""))

    def test_019_missing_transform_identity_rejected(self):
        with self.assertRaises(WordCoreError):
            calculate_hebrew("ברא", identities=ids("standard", transform=""))

    def test_020_missing_profile_identity_rejected(self):
        with self.assertRaises(WordCoreError):
            calculate_hebrew("ברא", identities=ids("standard", profile=""))

    def test_021_unknown_scheme_rejected(self):
        with self.assertRaises(WordCoreError):
            calculate_hebrew("ברא", identities=ids("mixed"))

    def test_022_identity_mismatch_rejected(self):
        with self.assertRaises(WordCoreError):
            calculate_hebrew("ברא", identities=ids("standard"), expected_identities=ids("standard", profile="other"))

    def test_023_transliteration_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_hebrew("bereshit", maqaf_mode="join")

    def test_024_mixed_hebrew_latin_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_hebrew("בראשית A", maqaf_mode="join")

    def test_025_numbers_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_hebrew("בראשית 1", maqaf_mode="join")

    def test_026_empty_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_hebrew("", maqaf_mode="join")

    def test_027_marks_only_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_hebrew("ְֱֲ", maqaf_mode="join")

    def test_028_punctuation_ignored_without_inventing_letters(self):
        self.assertEqual(transform_hebrew("ברא, אלהים!", maqaf_mode="join"), "ברא אלהים")

    def test_029_greek_diacritic_and_case_normalization(self):
        self.assertEqual(transform_greek("ἘΝ ἀρχῇ"), "εν αρχη")

    def test_030_greek_final_sigma_fold(self):
        self.assertEqual(transform_greek("λόγος"), "λογοσ")

    def test_031_greek_transliteration_rejected(self):
        with self.assertRaises(WordCoreError):
            transform_greek("logos")

    def test_032_greek_numeric_profile_held(self):
        with self.assertRaises(WordCoreError):
            IdentityBundle("s", "t", "p", "greek", "isopsephy").validate()

    def test_033_digital_root(self):
        self.assertEqual((digital_root(0), digital_root(2701), digital_root(4631)), (0, 1, 5))

    def test_034_surface_hash_matches_legacy_witness(self):
        calc = transform_hebrew(POINTED_GEN_1_1, maqaf_mode="join")
        self.assertEqual(hashlib.sha256(calc.encode("utf-8")).hexdigest(), "e6eff815ea17a7b0acdefbda37a41b0481ea804b23ea982eab5ed427a5cfe3a2")

    def test_035_output_is_json_serializable(self):
        r = calculate_hebrew(POINTED_GEN_1_1, identities=ids("standard"))
        json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False)

    def test_036_genesis_1_2_standard(self):
        text = "והארץ היתה תהו ובהו וחשך עלפני תהום ורוח אלהים מרחפת עלפני המים"
        r = calculate_hebrew(text, identities=ids("standard"))
        self.assertEqual((r["word_count"], r["letter_count"], r["total"], r["binary"]), (12, 52, 3546, "110111011010"))

    def test_037_genesis_1_2_gadol(self):
        text = "והארץ היתה תהו ובהו וחשך עלפני תהום ורוח אלהים מרחפת עלפני המים"
        self.assertEqual(calculate_hebrew(text, identities=ids("gadol"))["total"], 6516)

    def test_038_genesis_1_2_source_witness(self):
        text = "והארץ היתה תהו ובהו וחשך עלפני תהום ורוח אלהים מרחפת עלפני המים"
        self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), "92f5d6d58db081f1004c858bddf600a04f0ce02c24bc0a6111f9e31dfdc5be58")

    def test_039_genesis_1_7_standard(self):
        text = "ויעש אלהים אתהרקיע ויבדל בין המים אשר מתחת לרקיע ובין המים אשר מעל לרקיע ויהיכן"
        r = calculate_hebrew(text, identities=ids("standard"))
        self.assertEqual((r["word_count"], r["letter_count"], r["total"], r["binary"]), (15, 65, 4541, "1000110111101"))

    def test_040_genesis_1_7_gadol(self):
        text = "ויעש אלהים אתהרקיע ויבדל בין המים אשר מתחת לרקיע ובין המים אשר מעל לרקיע ויהיכן"
        self.assertEqual(calculate_hebrew(text, identities=ids("gadol"))["total"], 8171)

    def test_041_genesis_1_7_source_witness(self):
        text = "ויעש אלהים אתהרקיע ויבדל בין המים אשר מתחת לרקיע ובין המים אשר מעל לרקיע ויהיכן"
        self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), "b13c7aa63d2f66566f3071bfe075d8e81afead8e169bc886eb54aa2e05079bdd")

    def test_042_week_binary_round_trip_historical_value(self):
        self.assertEqual(int("11011000000001001", 2), 110601)

    def test_043_greek_iota_subscript_mark_is_stripped_before_casefold(self):
        self.assertEqual(transform_greek("ῇ"), "η")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WordCoreReferenceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "schema": "qel.word-core-reference-test-results/v2",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "status": "PASS" if result.wasSuccessful() else "FAIL",
    }
    (HERE / "WORD_CORE_REFERENCE_TEST_RESULTS.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    raise SystemExit(0 if result.wasSuccessful() else 1)
