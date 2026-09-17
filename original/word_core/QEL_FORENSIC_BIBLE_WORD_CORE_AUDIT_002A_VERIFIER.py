#!/usr/bin/env python3
"""QEL forensic Bible/WORD_CORE audit 002A reference verifier.

This standard-library verifier independently recomputes the exact available
Genesis anchors, transform behavior, value maps, negative/fail-closed cases,
and historical receipt consistency. It does NOT claim to be the original
8,701-byte Creation Week replay verifier, and it cannot reproduce the complete
16,079-comparison replay without the exact 1,658,780-byte JSON source body.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any

HEBREW_ORDER = "אבגדהוזחטיכלמנסעפצקרשת"
FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
STD_BASE = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7,
    "ח": 8, "ט": 9, "י": 10, "כ": 20, "ל": 30, "מ": 40,
    "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90, "ק": 100,
    "ר": 200, "ש": 300, "ת": 400,
}
STD = dict(STD_BASE)
for final, base in FINAL_TO_BASE.items():
    STD[final] = STD_BASE[base]
GAD = dict(STD)
GAD.update({"ך": 500, "ם": 600, "ן": 700, "ף": 800, "ץ": 900})
ORD = {ch: idx for idx, ch in enumerate(HEBREW_ORDER, 1)}
for final, base in FINAL_TO_BASE.items():
    ORD[final] = ORD[base]
RED = {ch: (0 if value == 0 else 1 + (value - 1) % 9) for ch, value in STD.items()}
HEBREW_LETTERS = frozenset(STD)

EXPECTED_CONTEXT = {
    "source_id": "QEL-GENESIS-CREATION-WEEK-SOURCE-SURFACES-V1",
    "transform_id": "QEL-WORD-CORE-HEBREW-LETTERS-MAQAF-V1",
    "profile_id": "qel_gematria_core_profile_v1",
    "profile_legacy_sha256": "04b534a91c7f49458ee01c9f4d2cb28faf85f09dba19bef98f9953b7f70a63de",
}
VALID_SCHEMES = {"mispar_hechrechi": "standard", "mispar_gadol": "gadol"}

GEN_1_1_POINTED = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
GEN_1_1_GOV = "בראשית ברא אלהים את השמים ואת הארץ"
GEN_1_2_GOV = "והארץ היתה תהו ובהו וחשך עלפני תהום ורוח אלהים מרחפת עלפני המים"
GEN_1_2_COMP = "והארץ היתה תהו ובהו וחשך על פני תהום ורוח אלהים מרחפת על פני המים"
GEN_1_7_GOV = "ויעש אלהים אתהרקיע ויבדל בין המים אשר מתחת לרקיע ובין המים אשר מעל לרקיע ויהיכן"

HISTORICAL = {
    "creation_week_json": {
        "bytes": 1_658_780,
        "sha256": "59cd4e30556b0ac665780825c0b81ff4e27f5d230c3139c890ce464d03330de0",
        "mounted": False,
    },
    "creation_week_replay_verifier": {
        "bytes": 8_701,
        "sha256": "84a84cb29a2cc89f8232f87d18aeaf6b07a081e6a0cbab4a68f667c92a495481",
        "mounted": False,
    },
    "creation_week_replay_report": {
        "bytes": 852,
        "sha256": "9825947d38692d7253e66e1184e713116248f6a6fe3d605f63690b76bd7dacd3",
        "comparisons": 16_079,
        "errors": 0,
    },
    "profile": {
        "bytes": 12_113,
        "correct_sha256": "04b534a91c7f49458ee01c9f4d2cb28faf85f09dba19bef98f9953b7f70a63de",
        "prior_b01_3_recorded_sha256": "04b5341c24ea35a1f1353d3be4ba27b581967b94b468b3d80f97ea0854307270",
    },
    "gematria_code": {
        "bytes": 8_384,
        "correct_sha256": "28b7eaa285a5c611dffcd73581d23182bddd135e8ddc2ae88b0e6f5026de391a",
        "prior_b01_3_recorded_sha256": "28b7ea36921db76c033e2cfad7a9760716a1cedac7419ae08498387a9ac1a08e",
    },
    "transform_code": {
        "bytes": 7_644,
        "correct_sha256": "be660146e071169c555f49ae6fc46752bee8f88b21f4b4615f56c25701fa7680",
        "prior_b01_3_recorded_sha256": "be6601ee362e0803dcb9b1d758f785c3af3397bec9128ee6aeb53985c402ed24",
    },
}

class AuditError(ValueError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def terminal_root(value: int) -> int:
    return 0 if value == 0 else 1 + (value - 1) % 9


def validate_context(context: dict[str, Any]) -> None:
    for field in ("source_id", "transform_id", "profile_id", "profile_legacy_sha256", "scheme", "finals_mode"):
        value = context.get(field)
        if not isinstance(value, str) or not value:
            raise AuditError(f"missing or empty context field: {field}")
    for field, expected in EXPECTED_CONTEXT.items():
        if context[field] != expected:
            raise AuditError(f"{field} mismatch")
    scheme = context["scheme"]
    if scheme not in VALID_SCHEMES:
        raise AuditError("unknown scheme")
    if context["finals_mode"] != VALID_SCHEMES[scheme]:
        raise AuditError("scheme/finals mode mismatch")


def transform_hebrew(raw: str, *, maqaf_mode: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise AuditError("source text must be a non-empty string")
    if maqaf_mode not in {"join", "split"}:
        raise AuditError("unknown maqaf mode")
    out: list[str] = []
    for ch in raw:
        if ch in HEBREW_LETTERS:
            out.append(ch)
        elif ch == "\u05be":  # Hebrew maqaf
            if maqaf_mode == "split":
                out.append(" ")
        elif ch.isspace():
            out.append(" ")
        elif unicodedata.category(ch) in {"Mn", "Mc", "Me", "Po", "Pd"}:
            # Combining marks and declared punctuation are non-calculation data.
            continue
        elif unicodedata.category(ch) == "Cf":
            raise AuditError("format/bidirectional control character rejected")
        else:
            raise AuditError(f"non-Hebrew calculation character rejected: U+{ord(ch):04X}")
    result = " ".join("".join(out).split())
    if not result:
        raise AuditError("calculation surface is empty")
    return result


def analyze_surface(surface: str) -> dict[str, Any]:
    if not surface:
        raise AuditError("empty calculation surface")
    if any(ch not in HEBREW_LETTERS and ch != " " for ch in surface):
        raise AuditError("calculation surface contains undeclared characters")
    words = surface.split()
    if not words:
        raise AuditError("no Hebrew words")
    letters = [ch for ch in surface if ch in HEBREW_LETTERS]
    standard_values = [STD[ch] for ch in letters]
    gadol_values = [GAD[ch] for ch in letters]
    ordinal_values = [ORD[ch] for ch in letters]
    reduced_values = [RED[ch] for ch in letters]
    standard_total = sum(standard_values)
    gadol_total = sum(gadol_values)
    return {
        "word_count": len(words),
        "letter_count": len(letters),
        "words": words,
        "word_standard_totals": [sum(STD[ch] for ch in word) for word in words],
        "word_gadol_totals": [sum(GAD[ch] for ch in word) for word in words],
        "standard_total": standard_total,
        "gadol_total": gadol_total,
        "gadol_delta": gadol_total - standard_total,
        "ordinal_total": sum(ordinal_values),
        "reduced_letter_total": sum(reduced_values),
        "terminal_katan": terminal_root(standard_total),
        "binary": format(standard_total, "b"),
        "hex": format(standard_total, "X"),
        "octal": format(standard_total, "o"),
        "binary_round_trip": int(format(standard_total, "b"), 2),
        "final_letter_count": sum(1 for ch in letters if ch in FINAL_TO_BASE),
        "letter_sequence": "".join(letters),
        "sha256_utf8": sha256_text(surface),
    }


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(check_id: str, category: str, description: str, actual: Any, expected: Any) -> None:
        passed = actual == expected
        checks.append({
            "id": check_id,
            "category": category,
            "description": description,
            "status": "PASS" if passed else "FAIL",
            "expected": expected,
            "actual": actual,
        })

    def expect_reject(check_id: str, description: str, fn) -> None:
        try:
            fn()
        except AuditError as exc:
            checks.append({"id": check_id, "category": "FAIL_CLOSED", "description": description,
                           "status": "PASS", "expected": "REJECT", "actual": f"REJECT:{exc}"})
        else:
            checks.append({"id": check_id, "category": "FAIL_CLOSED", "description": description,
                           "status": "FAIL", "expected": "REJECT", "actual": "ACCEPT"})

    # Genesis 1:1 exact-byte and transform anchor.
    calc_raw = transform_hebrew(GEN_1_1_POINTED, maqaf_mode="join")
    calc_nfc = transform_hebrew(unicodedata.normalize("NFC", GEN_1_1_POINTED), maqaf_mode="join")
    calc_nfd = transform_hebrew(unicodedata.normalize("NFD", GEN_1_1_POINTED), maqaf_mode="join")
    g11 = analyze_surface(calc_raw)
    check("A001", "RAW_IDENTITY", "Genesis 1:1 pointed display code points", len(GEN_1_1_POINTED), 65)
    check("A002", "RAW_IDENTITY", "Genesis 1:1 pointed display UTF-8 bytes", len(GEN_1_1_POINTED.encode("utf-8")), 124)
    check("A003", "RAW_IDENTITY", "Genesis 1:1 exact pointed-display SHA-256 witness", sha256_text(GEN_1_1_POINTED), "707c96583d95fb1957b4916673ab36ec2d6cfdc168b97a7f7e2125f4d0f23647")
    check("A004", "UNICODE", "NFC changes the raw pointed-byte witness", sha256_text(unicodedata.normalize("NFC", GEN_1_1_POINTED)) != sha256_text(GEN_1_1_POINTED), True)
    check("A005", "UNICODE", "NFD changes the raw pointed-byte witness", sha256_text(unicodedata.normalize("NFD", GEN_1_1_POINTED)) != sha256_text(GEN_1_1_POINTED), True)
    check("A006", "TRANSFORM", "Exact raw transform equals governing consonantal surface", calc_raw, GEN_1_1_GOV)
    check("A007", "TRANSFORM", "NFC transform preserves calculation surface", calc_nfc, GEN_1_1_GOV)
    check("A008", "TRANSFORM", "NFD transform preserves calculation surface", calc_nfd, GEN_1_1_GOV)
    check("A009", "TRANSFORM", "Genesis 1:1 calculation-surface code points", len(GEN_1_1_GOV), 34)
    check("A010", "TRANSFORM", "Genesis 1:1 calculation-surface UTF-8 bytes", len(GEN_1_1_GOV.encode("utf-8")), 62)
    check("A011", "TRANSFORM", "Genesis 1:1 calculation-surface SHA-256 witness", g11["sha256_utf8"], "e6eff815ea17a7b0acdefbda37a41b0481ea804b23ea982eab5ed427a5cfe3a2")
    check("A012", "ARITHMETIC", "Genesis 1:1 word count", g11["word_count"], 7)
    check("A013", "ARITHMETIC", "Genesis 1:1 letter count", g11["letter_count"], 28)
    check("A014", "ARITHMETIC", "Genesis 1:1 standard total", g11["standard_total"], 2701)
    check("A015", "ARITHMETIC", "Genesis 1:1 separate Gadol total", g11["gadol_total"], 4631)
    check("A016", "ARITHMETIC", "Genesis 1:1 Gadol delta", g11["gadol_delta"], 1930)
    check("A017", "ARITHMETIC", "Genesis 1:1 ordinal total", g11["ordinal_total"], 298)
    check("A018", "ARITHMETIC", "Genesis 1:1 reduced-letter total", g11["reduced_letter_total"], 82)
    check("A019", "ARITHMETIC", "Genesis 1:1 terminal root", g11["terminal_katan"], 1)
    check("A020", "ENCODING", "Genesis 1:1 binary", g11["binary"], "101010001101")
    check("A021", "ENCODING", "Genesis 1:1 hexadecimal", g11["hex"], "A8D")
    check("A022", "ENCODING", "Genesis 1:1 octal", g11["octal"], "5215")
    check("A023", "ENCODING", "Genesis 1:1 binary round trip", g11["binary_round_trip"], 2701)
    check("A024", "ARITHMETIC", "Genesis 1:1 word totals", g11["word_standard_totals"], [913, 203, 86, 401, 395, 407, 296])
    check("A025", "ARITHMETIC", "Genesis 1:1 word totals sum", sum(g11["word_standard_totals"]), 2701)
    check("A026", "FINAL_FORMS", "Genesis 1:1 final-letter count", g11["final_letter_count"], 3)
    check("A027", "FINAL_FORMS", "Genesis 1:1 final-form delta decomposition", (600-40)+(600-40)+(900-90), 1930)
    check("A028", "MUTATION", "Removing vav changes ואת to את", analyze_surface("ואת")["standard_total"], 407)
    check("A029", "MUTATION", "Mutation target את standard total", analyze_surface("את")["standard_total"], 401)
    check("A030", "MUTATION", "Mutation changes binary", [analyze_surface("ואת")["binary"], analyze_surface("את")["binary"]], ["110010111", "110010001"])

    # Genesis 1:2 governing/component lane invariance.
    g12 = analyze_surface(GEN_1_2_GOV)
    c12 = analyze_surface(GEN_1_2_COMP)
    check("B001", "TRANSFORM", "Genesis 1:2 governing surface SHA-256 witness", g12["sha256_utf8"], "92f5d6d58db081f1004c858bddf600a04f0ce02c24bc0a6111f9e31dfdc5be58")
    check("B002", "TRANSFORM", "Genesis 1:2 component surface SHA-256 witness", c12["sha256_utf8"], "2edf0b6aa056add964a465e562c22273d4b6032e2bf723a16e04bb1cd916d16d")
    check("B003", "TOKENIZATION", "Genesis 1:2 governing word count", g12["word_count"], 12)
    check("B004", "TOKENIZATION", "Genesis 1:2 component word count", c12["word_count"], 14)
    check("B005", "TOKENIZATION", "Genesis 1:2 lane letter counts", [g12["letter_count"], c12["letter_count"]], [52, 52])
    check("B006", "ARITHMETIC", "Genesis 1:2 lane standard totals", [g12["standard_total"], c12["standard_total"]], [3546, 3546])
    check("B007", "ARITHMETIC", "Genesis 1:2 lane Gadol totals", [g12["gadol_total"], c12["gadol_total"]], [6516, 6516])
    check("B008", "FINAL_FORMS", "Genesis 1:2 Gadol delta", g12["gadol_delta"], 2970)
    check("B009", "ARITHMETIC", "Genesis 1:2 ordinal total", g12["ordinal_total"], 576)
    check("B010", "ARITHMETIC", "Genesis 1:2 reduced-letter total", g12["reduced_letter_total"], 234)
    check("B011", "ARITHMETIC", "Genesis 1:2 terminal root", g12["terminal_katan"], 9)
    check("B012", "ENCODING", "Genesis 1:2 binary", g12["binary"], "110111011010")
    check("B013", "ENCODING", "Genesis 1:2 hexadecimal", g12["hex"], "DDA")
    check("B014", "ENCODING", "Genesis 1:2 octal", g12["octal"], "6732")
    check("B015", "ENCODING", "Genesis 1:2 binary round trip", g12["binary_round_trip"], 3546)
    check("B016", "TOKENIZATION", "Genesis 1:2 lanes preserve letter sequence", g12["letter_sequence"], c12["letter_sequence"])

    maqaf_raw = "על־פני"
    maqaf_join = transform_hebrew(maqaf_raw, maqaf_mode="join")
    maqaf_split = transform_hebrew(maqaf_raw, maqaf_mode="split")
    check("B017", "TOKENIZATION", "Maqaf join transform", maqaf_join, "עלפני")
    check("B018", "TOKENIZATION", "Maqaf split transform", maqaf_split, "על פני")
    check("B019", "TOKENIZATION", "Maqaf lane standard invariance", [analyze_surface(maqaf_join)["standard_total"], analyze_surface(maqaf_split)["standard_total"]], [240, 240])
    check("B020", "TOKENIZATION", "Maqaf lane Gadol invariance", [analyze_surface(maqaf_join)["gadol_total"], analyze_surface(maqaf_split)["gadol_total"]], [240, 240])

    # Genesis 1:7 selective replay anchor from the accepted parent record.
    g17 = analyze_surface(GEN_1_7_GOV)
    check("C001", "TRANSFORM", "Genesis 1:7 governing surface SHA-256 witness", g17["sha256_utf8"], "b13c7aa63d2f66566f3071bfe075d8e81afead8e169bc886eb54aa2e05079bdd")
    check("C002", "ARITHMETIC", "Genesis 1:7 word count", g17["word_count"], 15)
    check("C003", "ARITHMETIC", "Genesis 1:7 letter count", g17["letter_count"], 65)
    check("C004", "ARITHMETIC", "Genesis 1:7 standard total", g17["standard_total"], 4541)
    check("C005", "ARITHMETIC", "Genesis 1:7 Gadol total", g17["gadol_total"], 8171)
    check("C006", "FINAL_FORMS", "Genesis 1:7 Gadol delta", g17["gadol_delta"], 3630)
    check("C007", "ARITHMETIC", "Genesis 1:7 ordinal total", g17["ordinal_total"], 761)
    check("C008", "ARITHMETIC", "Genesis 1:7 reduced-letter total", g17["reduced_letter_total"], 212)
    check("C009", "ARITHMETIC", "Genesis 1:7 terminal root", g17["terminal_katan"], 5)
    check("C010", "ENCODING", "Genesis 1:7 binary", g17["binary"], "1000110111101")
    check("C011", "ENCODING", "Genesis 1:7 hexadecimal", g17["hex"], format(4541, "X"))
    check("C012", "ENCODING", "Genesis 1:7 octal", g17["octal"], format(4541, "o"))
    check("C013", "ENCODING", "Genesis 1:7 binary round trip", g17["binary_round_trip"], 4541)

    # Historical week-level receipt consistency. These are record-level checks,
    # not a fresh 34-verse replay.
    week_standard = 110_601
    week_gadol = 205_511
    check("D001", "HISTORICAL_RECEIPT", "Week standard binary", format(week_standard, "b"), "11011000000001001")
    check("D002", "HISTORICAL_RECEIPT", "Week standard hexadecimal", format(week_standard, "X"), "1B009")
    check("D003", "HISTORICAL_RECEIPT", "Week standard octal", format(week_standard, "o"), "330011")
    check("D004", "HISTORICAL_RECEIPT", "Week standard terminal root", terminal_root(week_standard), 9)
    check("D005", "HISTORICAL_RECEIPT", "Week Gadol-standard delta", week_gadol - week_standard, 94_910)
    check("D006", "HISTORICAL_RECEIPT", "Standard and Gadol remain separate", week_standard != week_gadol, True)
    check("D007", "HISTORICAL_RECEIPT", "Recorded verse count", 34, 34)
    check("D008", "HISTORICAL_RECEIPT", "Recorded governing words", 391, 391)
    check("D009", "HISTORICAL_RECEIPT", "Recorded calculation letters", 1815, 1815)
    check("D010", "HISTORICAL_RECEIPT", "Recorded component-lane words", 469, 469)
    check("D011", "HISTORICAL_RECEIPT", "Recorded independent comparisons", HISTORICAL["creation_week_replay_report"]["comparisons"], 16_079)
    check("D012", "HISTORICAL_RECEIPT", "Recorded replay errors", HISTORICAL["creation_week_replay_report"]["errors"], 0)
    check("D013", "HISTORICAL_RECEIPT", "Recorded correction tests", "20/20 PASS", "20/20 PASS")

    # Strict context tests.
    standard_context = dict(EXPECTED_CONTEXT, scheme="mispar_hechrechi", finals_mode="standard")
    gadol_context = dict(EXPECTED_CONTEXT, scheme="mispar_gadol", finals_mode="gadol")
    try:
        validate_context(standard_context)
        accepted_standard = True
    except AuditError:
        accepted_standard = False
    try:
        validate_context(gadol_context)
        accepted_gadol = True
    except AuditError:
        accepted_gadol = False
    check("E001", "FAIL_CLOSED", "Valid standard context accepted", accepted_standard, True)
    check("E002", "FAIL_CLOSED", "Valid Gadol context accepted", accepted_gadol, True)
    for idx, field in enumerate(("source_id", "transform_id", "profile_id", "profile_legacy_sha256", "scheme", "finals_mode"), 3):
        invalid = dict(standard_context)
        invalid.pop(field)
        expect_reject(f"E{idx:03d}", f"Missing {field} rejected", lambda invalid=invalid: validate_context(invalid))
    expect_reject("E009", "Unknown source identity rejected", lambda: validate_context(dict(standard_context, source_id="unknown")))
    expect_reject("E010", "Unknown transform identity rejected", lambda: validate_context(dict(standard_context, transform_id="unknown")))
    expect_reject("E011", "Unknown profile identity rejected", lambda: validate_context(dict(standard_context, profile_id="unknown")))
    expect_reject("E012", "Unknown scheme rejected", lambda: validate_context(dict(standard_context, scheme="unknown")))
    expect_reject("E013", "Mixed standard/Gadol mode rejected", lambda: validate_context(dict(standard_context, finals_mode="gadol")))
    expect_reject("E014", "Prior B01.3 incorrect profile witness rejected", lambda: validate_context(dict(standard_context, profile_legacy_sha256=HISTORICAL["profile"]["prior_b01_3_recorded_sha256"])))
    expect_reject("E015", "Transliteration rejected as calculation input", lambda: transform_hebrew("bereshit bara", maqaf_mode="join"))
    expect_reject("E016", "Mixed Latin character rejected", lambda: transform_hebrew("בראשיתA", maqaf_mode="join"))
    expect_reject("E017", "Bidirectional control rejected", lambda: transform_hebrew("בראשית\u202e", maqaf_mode="join"))
    expect_reject("E018", "Empty input rejected", lambda: transform_hebrew("", maqaf_mode="join"))
    expect_reject("E019", "Unknown maqaf mode rejected", lambda: transform_hebrew("בראשית", maqaf_mode="unknown"))

    # Corrective custody comparison: prior B01.3 recorded three nonmatching
    # legacy witnesses. Exact source bytes remain unmounted, so this confirms
    # the record discrepancy, not the contents of the files.
    check("F001", "CUSTODY_CORRECTION", "Profile legacy witness discrepancy detected", HISTORICAL["profile"]["prior_b01_3_recorded_sha256"] != HISTORICAL["profile"]["correct_sha256"], True)
    check("F002", "CUSTODY_CORRECTION", "Gematria-code legacy witness discrepancy detected", HISTORICAL["gematria_code"]["prior_b01_3_recorded_sha256"] != HISTORICAL["gematria_code"]["correct_sha256"], True)
    check("F003", "CUSTODY_CORRECTION", "Transform-code legacy witness discrepancy detected", HISTORICAL["transform_code"]["prior_b01_3_recorded_sha256"] != HISTORICAL["transform_code"]["correct_sha256"], True)
    check("F004", "CUSTODY", "Creation Week JSON exact bytes are not mounted", HISTORICAL["creation_week_json"]["mounted"], False)
    check("F005", "CUSTODY", "Original replay verifier exact bytes are not mounted", HISTORICAL["creation_week_replay_verifier"]["mounted"], False)

    passed = sum(item["status"] == "PASS" for item in checks)
    failed = len(checks) - passed
    by_category: dict[str, dict[str, int]] = {}
    for item in checks:
        bucket = by_category.setdefault(item["category"], {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed" if item["status"] == "PASS" else "failed"] += 1

    return {
        "schema": "qel.forensic-bible-word-core-audit-002a-results/v1",
        "audit_id": "QEL-FORENSIC-BIBLE-WORD-CORE-AUDIT-002A",
        "timestamp_et": "2026-08-18T13:17:00-04:00",
        "result": "PASS" if failed == 0 else "FAIL",
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks_failed": failed,
        "category_totals": by_category,
        "fresh_full_16079_replay_performed": False,
        "fresh_full_16079_replay_blocker": "Exact 1,658,780-byte JSON and exact 8,701-byte original verifier are File Library references but are not mounted as runtime bytes.",
        "historical_full_replay_record": {
            "status": "PASS_AS_RECORDED_NOT_FRESHLY_REEXECUTED",
            "comparisons": 16_079,
            "errors": 0,
            "verses": 34,
            "governing_words": 391,
            "component_words": 469,
            "letters": 1815,
            "standard_total": 110_601,
            "gadol_total": 205_511,
        },
        "exact_artifact_references": HISTORICAL,
        "computed_anchors": {"Genesis 1:1": g11, "Genesis 1:2 governing": g12, "Genesis 1:2 component": c12, "Genesis 1:7": g17},
        "checks": checks,
        "claim_boundary": "Reference-harness and anchor calculations pass. Original WORD_CORE code and full Creation Week replay remain SOURCE_BYTES_REQUIRED until exact bytes are mounted and executed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("audit_id", "result", "checks_total", "checks_passed", "checks_failed")}, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
