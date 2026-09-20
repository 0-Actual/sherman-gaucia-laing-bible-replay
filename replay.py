#!/usr/bin/env python3
"""New 2026-09-17 offline replay adapter; recovered WORD_CORE remains unchanged.

This replays saved text and arithmetic, not the original model inference.
Python 3.10+; standard library only; no network, signatures, or fingerprints.
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
import uuid
from pathlib import Path
import re
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
SCHEMES = ("standard", "gadol", "ordinal", "reduced")
# Word-group lengths explicitly described in each recovered study's arithmetic
# paragraph. These are lexical boundaries, not newly inferred meanings.
CLAUSE_WORD_LENGTHS = {"Genesis 1:2": [4, 4, 6], "Genesis 1:3": [2, 2, 2],
                       "Genesis 1:4": [6, 6], "Genesis 1:5": [7, 6]}
# Limited new reference profile: only values stated in the recovered studies'
# selected Greek-word traces. It does not activate the recovered draft profile.
GREEK_VALUES = {
    "α": 1, "γ": 3, "ε": 5, "η": 8, "κ": 20, "λ": 30, "μ": 40,
    "ν": 50, "ο": 70, "π": 80, "ρ": 100, "σ": 200, "υ": 400,
    "φ": 500, "ω": 800,
}


class ReplayError(ValueError):
    pass



def require(value, kind, location: str):
    """Validate JSON types explicitly; bool is never an integer count/value."""
    if type(value) is not kind:
        raise ReplayError(f"{location}: expected {kind.__name__}")
    if kind in (str, list, dict) and not value:
        raise ReplayError(f"{location}: must not be empty")
    if kind is int and value < 0:
        raise ReplayError(f"{location}: must be nonnegative")
    return value


def validate_document(document, filename: str) -> dict:
    require(document, dict, filename)
    require(document.get("lesson_markdown"), str, filename + ".lesson_markdown")
    if ("text_and_calculations" in document) == ("word_core" in document):
        raise ReplayError(f"{filename}: exactly one calculation record is required")
    calc = document.get("text_and_calculations", document.get("word_core"))
    require(calc, dict, filename + ".calculations")
    for key in ("passage", "hebrew_pointed", "hebrew_consonantal", "kjv"):
        require(calc.get(key), str, filename + "." + key)
    passage = calc["passage"]
    if passage not in {f"Genesis 1:{verse}" for verse in range(1, 6)}:
        raise ReplayError(f"{filename}: unsupported passage {passage!r}")
    for key in ("total", "consonantal_letter_count"):
        require(calc.get(key), int, filename + "." + key)
    require(calc.get("lexical_word_count", calc.get("word_count")), int, filename + ".word_count")
    words = require(calc.get("words"), list, filename + ".words")
    for index, row in enumerate(words):
        where = f"{filename}.words[{index}]"
        require(row, dict, where)
        require(row.get("hebrew"), str, where + ".hebrew")
        require(row.get("value"), int, where + ".value")
        for i, letter in enumerate(require(row.get("letter_values"), list, where + ".letter_values")):
            require(letter, dict, f"{where}.letter_values[{i}]")
            require(letter.get("letter"), str, where + ".letter")
            require(letter.get("value"), int, where + ".letter_value")
    # Every saved study, including the baseline, declares a Greek witness.
    greek = require(calc.get("selected_greek_witness"), dict, filename + ".selected_greek_witness")
    require(greek.get("word"), str, filename + ".greek.word")
    require(greek.get("total"), int, filename + ".greek.total")
    for index, row in enumerate(require(greek.get("trace"), list, filename + ".greek.trace")):
        require(row, dict, f"{filename}.greek.trace[{index}]")
        require(row.get("letter"), str, filename + ".greek.letter")
        require(row.get("value"), int, filename + ".greek.value")
    if passage == "Genesis 1:1":
        factors = require(calc.get("arithmetic_factorization"), list, filename + ".arithmetic_factorization")
        for item in factors:
            require(item, int, filename + ".factor")
    else:
        require(calc.get("pointed_whitespace_unit_count"), int, filename + ".pointed_whitespace_unit_count")
        clauses = require(calc.get("clause_subtotals"), list, filename + ".clause_subtotals")
        for item in clauses:
            require(item, int, filename + ".clause_subtotal")
        if len(clauses) != len(CLAUSE_WORD_LENGTHS[passage]):
            raise ReplayError(f"{filename}: wrong number of clause subtotals")
    if passage == "Genesis 1:4" or "prior_verse_comparison" in calc:
        prior = require(calc.get("prior_verse_comparison"), dict, filename + ".prior_verse_comparison")
        if passage != "Genesis 1:4":
            raise ReplayError(f"{filename}: prior comparison is only defined for Genesis 1:4")
        for key in ("prior_total", "current_second_clause_total"):
            require(prior.get(key), int, filename + "." + key)
    if passage == "Genesis 1:4" or "dictionary_form" in greek or "dictionary_form_total" in greek:
        require(greek.get("dictionary_form"), str, filename + ".greek.dictionary_form")
        require(greek.get("dictionary_form_total"), int, filename + ".greek.dictionary_form_total")
    validation = require(document.get("validation"), dict, filename + ".validation")
    require(validation.get("whitespace_word_count_lesson", validation.get("whitespace_word_count_total")),
            int, filename + ".validation.lesson_word_count")
    require(validation.get("whitespace_word_count_with_source_notes", validation.get("whitespace_word_count_with_notes",
            validation.get("whitespace_word_count_total"))), int, filename + ".validation.markdown_word_count")
    exposition = require(document.get("exposition", document.get("word_aux")), dict, filename + ".exposition")
    require(calc.get("transliteration", exposition.get("transliteration")), str, filename + ".transliteration")
    witnesses = require(exposition.get("new_testament_witnesses"), list, filename + ".new_testament_witnesses")
    for witness in witnesses:
        require(witness, str, filename + ".new_testament_witness")
    return calc


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReplayError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_document(path: Path, expected_passage: str) -> dict:
    def reject_constant(value):
        raise ReplayError(f"{path.name}: invalid JSON numeric constant {value}")
    document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=reject_constant)
    calc = validate_document(document, path.name)
    if calc["passage"] != expected_passage:
        raise ReplayError(f"{path.name}: expected passage {expected_passage}")
    return document


def atomic_json(path: Path, document: dict) -> None:
    """Replace one record only after its complete bytes have been written."""
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def output_lock(output: Path):
    """Cooperating writers only; a crash leaves the lock for explicit recovery."""
    output.parent.mkdir(parents=True, exist_ok=True)
    path = output.parent / ("." + output.name + ".replay.lock")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise ReplayError(f"Replay output is locked; inspect the existing run before recovery: {path}") from error
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "output": str(output)}) + "\n")
        yield
    finally:
        path.unlink(missing_ok=True)


def _status(run_id: str, state: str, status: str, **extra) -> dict:
    return {"schema": "qel-bible-replay-run/1", "attempt_id": run_id,
            "attempt_id_note": "Random local correlation label; not a fingerprint or signature",
            "state": state, "status": status, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "owner_signature": None, **extra}

def load_engine(path: Path):
    spec = importlib.util.spec_from_file_location("qel_recovered_word_core_v2", path)
    if spec is None or spec.loader is None:
        raise ReplayError("Unable to load the supplied recovered WORD_CORE module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_hebrew_input(raw: str, engine) -> None:
    """New strict boundary; no silent symbol removal before the old engine."""
    if not isinstance(raw, str) or not raw:
        raise ReplayError("Hebrew input must be a nonempty string")
    for char in unicodedata.normalize("NFD", raw):
        category = unicodedata.category(char)
        if char in engine.HEBREW_LETTERS or char in "\t\r\n" or char == "\u05be":
            continue
        if category.startswith("Z") or category.startswith("P"):
            continue
        if category.startswith("M") and "\u0591" <= char <= "\u05c7":
            continue
        raise ReplayError(f"Unsupported Hebrew input character U+{ord(char):04X}")


def hebrew_lanes(raw: str, source_id: str, engine, maqaf_mode: str = "split") -> dict:
    validate_hebrew_input(raw, engine)
    return engine.calculate_named_hebrew_lanes(
        raw, source_id=source_id,
        transform_id="recovered-WORD_CORE-reference-v2/NFD/maqaf-" + maqaf_mode,
        profile_id="recovered-WORD_CORE-reference-v2/four-Hebrew-schemes",
        maqaf_mode=maqaf_mode,
    )


def greek_selected_word(raw: str, engine) -> dict:
    """New limited arithmetic, using the recovered engine's Greek transform."""
    if not isinstance(raw, str) or not raw:
        raise ReplayError("Greek word must be a nonempty string")
    for char in unicodedata.normalize("NFD", raw):
        category = unicodedata.category(char)
        if category.startswith("M"):
            continue
        folded = char.casefold().replace("ς", "σ")
        if folded not in GREEK_VALUES:
            raise ReplayError(f"Character outside the declared selected-word Greek profile: {char!r}")
    surface = engine.transform_greek(raw)
    if not surface:
        raise ReplayError("Greek word has no letters after normalization")
    trace = [{"letter": char, "value": GREEK_VALUES[char]} for char in surface]
    return {
        "implementation": "new-20260917-selected-word-reference",
        "frozen_historical_numeric_profile_recovered": False,
        "historical_profile_note": "A historical draft Greek map is preserved separately; its allow_execution is false and its primary-text identity is unset. This new selected-word profile does not activate that draft.",
        "input": raw, "calculation_surface": surface,
        "trace": trace, "total": sum(row["value"] for row in trace),
    }


def compare(checks: list, name: str, actual, expected) -> None:
    checks.append({"check": name, "passed": actual == expected,
                   "actual": actual, "expected": expected})


def count_report(document: dict, markdown: str, baseline: int | None) -> dict:
    lesson = document["lesson_markdown"]
    validation = document.get("validation", {})
    expected = validation.get("whitespace_word_count_lesson",
                              validation.get("whitespace_word_count_total"))
    lesson_count = len(lesson.split())
    return {
        "method": "Python str.split() on saved Unicode text; count tokens; punctuation is not stripped",
        "lesson_words": lesson_count,
        "source_declared_lesson_words": expected,
        "markdown_words_including_any_notes": len(markdown.split()),
        "historical_preaching_count_not_recomputed": validation.get("whitespace_word_count_preaching"),
        "historical_preaching_count_note": "Source has no explicit machine-readable preaching boundary",
        "baseline_genesis_1_1_lesson_words": baseline,
        "ratio_to_genesis_1_1_baseline": round(lesson_count / baseline, 9) if baseline else None,
        "equals_twice_genesis_1_1_baseline": lesson_count == 2 * baseline if baseline else None,
        "baseline_scope": "The recovered Genesis 1:1 baseline only; no separate prior baseline is claimed for other verses",
    }


def study_replay(document: dict, markdown: str, filename: str, engine, baseline: int | None) -> dict:
    calc = validate_document(document, filename)
    require(markdown, str, filename + ".markdown")
    source_id = "public-study/" + filename
    lanes = hebrew_lanes(calc["hebrew_pointed"], source_id, engine)
    standard = lanes["standard"]
    checks: list[dict] = []
    compare(checks, "pointed_to_consonantal_surface", standard["calculation_surface"], calc["hebrew_consonantal"])
    compare(checks, "standard_total", standard["total"], calc["total"])
    compare(checks, "letter_count", standard["letter_count"], calc["consonantal_letter_count"])
    compare(checks, "lexical_word_count", standard["word_count"], calc.get("lexical_word_count", calc.get("word_count")))
    expected_rows = calc["words"]
    compare(checks, "word_spelling_trace", [row["token"] for row in standard["rows"]], [row["hebrew"] for row in expected_rows])
    compare(checks, "word_total_trace", [row["subtotal"] for row in standard["rows"]], [row["value"] for row in expected_rows])
    compare(checks, "letter_value_trace", [row["values"] for row in standard["rows"]],
            [[letter["value"] for letter in row["letter_values"]] for row in expected_rows])
    compare(checks, "letter_spelling_trace", [row["letters"] for row in standard["rows"]],
            [[letter["letter"] for letter in row["letter_values"]] for row in expected_rows])
    compare(checks, "NFC_and_NFD_equivalence", standard["calculation_surface"],
            hebrew_lanes(unicodedata.normalize("NFC", calc["hebrew_pointed"]), source_id, engine)["standard"]["calculation_surface"])
    joined = hebrew_lanes(calc["hebrew_pointed"], source_id, engine, "join")
    compare(checks, "maqaf_preserves_all_four_totals",
            [joined[s]["total"] for s in SCHEMES], [lanes[s]["total"] for s in SCHEMES])
    if "pointed_whitespace_unit_count" in calc:
        compare(checks, "pointed_whitespace_units", len(calc["hebrew_pointed"].split()), calc["pointed_whitespace_unit_count"])
    if "arithmetic_factorization" in calc:
        compare(checks, "declared_factor_product", math.prod(calc["arithmetic_factorization"]), standard["total"])
    clause_result = None
    if "clause_subtotals" in calc:
        lengths = CLAUSE_WORD_LENGTHS[calc["passage"]]
        cursor, subtotals = 0, []
        for length in lengths:
            subtotals.append(sum(row["subtotal"] for row in standard["rows"][cursor:cursor + length]))
            cursor += length
        clause_result = {"lexical_word_group_lengths": lengths, "subtotals": subtotals,
                         "boundary_source": "Arithmetic paragraph in the saved study"}
        compare(checks, "clause_subtotals", subtotals, calc["clause_subtotals"])
        compare(checks, "clause_partition_covers_verse", cursor, standard["word_count"])
    if "prior_verse_comparison" in calc:
        prior = calc["prior_verse_comparison"]
        # Known earlier verse source is quoted explicitly in the recovered
        # preceding study. Do not derive its expected value from current data.
        prior_result = hebrew_lanes("ויאמר אלהים יהי אור ויהי אור", "public-study/Genesis_1_3_Expanded_Study.json", engine)["standard"]["total"]
        compare(checks, "prior_verse_reference_total", prior_result, prior["prior_total"])
        compare(checks, "current_second_clause_total", clause_result["subtotals"][1], prior["current_second_clause_total"])
    greek_source = calc.get("selected_greek_witness")
    greek = greek_selected_word(greek_source["word"], engine) if greek_source else None
    if greek:
        compare(checks, "selected_greek_total", greek["total"], greek_source["total"])
        compare(checks, "selected_greek_letter_values", [r["value"] for r in greek["trace"]],
                [r["value"] for r in greek_source["trace"]])
        compare(checks, "selected_greek_letter_spellings", [r["letter"] for r in greek["trace"]],
                [r["letter"].replace("ς", "σ") for r in greek_source["trace"]])
        if "dictionary_form" in greek_source:
            dictionary = greek_selected_word(greek_source["dictionary_form"], engine)
            compare(checks, "selected_greek_dictionary_form", dictionary["total"], greek_source["dictionary_form_total"])
            greek["dictionary_form_replay"] = dictionary
    words = count_report(document, markdown, baseline)
    compare(checks, "saved_lesson_word_count", words["lesson_words"], words["source_declared_lesson_words"])
    validation = document.get("validation", {})
    expected_markdown_words = validation.get("whitespace_word_count_with_source_notes",
        validation.get("whitespace_word_count_with_notes", validation.get("whitespace_word_count_total")))
    if expected_markdown_words is not None:
        compare(checks, "saved_markdown_word_count", words["markdown_words_including_any_notes"], expected_markdown_words)
    # The complete lesson is a prefix of its Markdown file; any following notes
    # stay outside the measured lesson. No regenerated narrative is substituted.
    compare(checks, "saved_markdown_preserves_lesson", markdown.startswith(document["lesson_markdown"]), True)
    exposition = document.get("exposition", document.get("word_aux", {}))
    return {
        "passage": calc["passage"], "source_file": filename,
        "state": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "source_and_display": {
            "hebrew_pointed": calc["hebrew_pointed"], "kjv": calc["kjv"],
            "transliteration": calc.get("transliteration", exposition.get("transliteration")),
            "new_testament_witnesses": exposition.get("new_testament_witnesses"),
        },
        "calculation": {"hebrew_lanes": lanes,
                        "maqaf_join_word_count": joined["standard"]["word_count"],
                        "declared_clause_grouping": clause_result,
                        "selected_greek": greek},
        "interpretation": {"replayed_verbatim": True,
                           "authority": "Saved exposition; arithmetic does not verify theology or divine revelation",
                           "model_generation_replayed": False},
        "word_counts": words, "checks": checks,
    }


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    # Preserve the saved emphases; text marked bold is red as a reading aid.
    # No raw HTML or remote images from Markdown are executed.
    return re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', escaped)


def render_saved_verse(kjv: str, markdown: str) -> str:
    """Reuse source emphasis only from one exactly matching verse quotation."""
    matches = [line[2:].strip() for line in markdown.splitlines()
               if line.startswith("> ") and line[2:].strip().replace("**", "") == kjv]
    return inline_markdown(matches[0]) if len(matches) == 1 else html.escape(kjv)


def render_markdown(markdown: str) -> str:
    """Small local presentation layer; original .md remains authoritative."""
    parts: list[str] = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells):
                    tag = "th" if not rows else "td"
                    rows.append("<tr>" + "".join(f"<{tag}>{inline_markdown(c)}</{tag}>" for c in cells) + "</tr>")
                index += 1
            parts.append('<div class="table"><table>' + "".join(rows) + "</table></div>")
            continue
        if line.startswith("#"):
            marker = len(line) - len(line.lstrip("#"))
            level = min(6, max(2, marker + 1))
            parts.append(f"<h{level}>" + inline_markdown(line.lstrip("# ")) + f"</h{level}>")
        elif line.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].startswith(">"):
                quote.append(lines[index].lstrip("> "))
                index += 1
            parts.append("<blockquote>" + inline_markdown(" ".join(quote)) + "</blockquote>")
            continue
        elif line.startswith(("- ", "* ")):
            parts.append('<p class="item">• ' + inline_markdown(line[2:]) + "</p>")
        else:
            paragraph = [line]
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith(("#", "|", ">", "- ", "* ")):
                paragraph.append(lines[index])
                index += 1
            parts.append("<p>" + inline_markdown(" ".join(paragraph)) + "</p>")
            continue
        index += 1
    return "\n".join(parts)


def render_index(results: dict, documents: list[tuple[dict, str]]) -> str:
    sections = []
    navigation = []
    failed_comparisons = []
    for label, record in [("Baseline", results["baseline"]),
                          *[("Expanded study", row) for row in results["studies"]]]:
        for check in record["checks"]:
            if not check["passed"]:
                observed = html.escape(json.dumps(check["actual"], ensure_ascii=False))
                expected = html.escape(json.dumps(check["expected"], ensure_ascii=False))
                failed_comparisons.append(
                    f'<li><b>{label} · {html.escape(record["passage"])}</b> — '
                    f'{html.escape(check["check"].replace("_", " "))}: '
                    f'calculated {observed}; saved expected {expected}.</li>')
    failure_summary = ('<p>Failed source comparisons:</p><ul>' + "".join(failed_comparisons) + '</ul>'
                       if failed_comparisons else '<p>No failed source comparisons.</p>')
    status_html = (
        '<div class="replay-status" role="status" aria-labelledby="replay-status-heading">'
        '<h2 id="replay-status-heading">Replay verification</h2>'
        f'<p>Overall replay status: <strong>{html.escape(results["status"])}</strong>.</p>'
        f'<p>Required Genesis 1:1 baseline status: <strong>{html.escape(results["baseline"]["state"])}</strong>.</p>'
        + failure_summary + '</div>')
    for index, (result, (_, markdown)) in enumerate(zip(results["studies"], documents), 1):
        passage = html.escape(result["passage"])
        navigation.append(f'<a href="#study-{index}">{passage}</a>')
        display = result["source_and_display"]
        totals = result["calculation"]["hebrew_lanes"]
        rows = "".join(f'<tr><td>{name.capitalize()}</td><td>{totals[name]["total"]:,}</td></tr>' for name in SCHEMES)
        trace_rows = "".join('<tr><td dir="rtl">' + html.escape(row["token"]) + "</td><td>" +
                             " + ".join(map(str, row["values"])) + f'</td><td>{row["subtotal"]}</td></tr>'
                             for row in totals["standard"]["rows"])
        greek = result["calculation"]["selected_greek"]
        greek_html = (f'<p>Selected Greek word: <b>{html.escape(greek["input"])}</b> = {greek["total"]:,}. '
                      'Replayed with the new limited reference profile.</p>') if greek else ""
        wc = result["word_counts"]
        sections.append(f'''<section id="study-{index}"><div class="eyebrow">Saved study · arithmetic replay {result["state"]}</div>
<h2>{passage}</h2><p class="hebrew" lang="he" dir="rtl">{html.escape(display["hebrew_pointed"])}</p>
<p class="transliteration">{html.escape(display["transliteration"] or "")}</p>
<blockquote>{render_saved_verse(display["kjv"], markdown)}</blockquote><p class="caption">King James Version · saved source text</p>
<div class="metrics"><span><b>{wc["lesson_words"]:,}</b> lesson words</span><span><b>{totals["standard"]["word_count"]}</b> Hebrew lexical words</span><span><b>{totals["standard"]["letter_count"]}</b> consonants</span></div>
<details><summary>Inspect arithmetic, word counts, and checks</summary><table><tr><th>Hebrew convention</th><th>Total</th></tr>{rows}</table>
<p>Maqaf split for lexical words; join gives {result["calculation"]["maqaf_join_word_count"]} units. All four totals remain unchanged.</p>
<table><tr><th>Word</th><th>Letter values</th><th>Standard total</th></tr>{trace_rows}</table>{greek_html}
<p>Lesson/baseline ratio: {wc["ratio_to_genesis_1_1_baseline"]}. The available baseline is Genesis 1:1 ({wc["baseline_genesis_1_1_lesson_words"]:,} words). Other verses have no separately recovered earlier baseline.</p>
<p>{len(result["checks"])} source comparison checks; state {result["state"]}. Full traces are in results.json.</p></details>
<details class="lesson"><summary>Read the complete expanded study</summary>{render_markdown(markdown)}</details></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
<title>QEL · The Genesis Studies</title><style>
:root{color-scheme:light;--ink:#202d3a;--paper:#f7f3e9;--accent:#7b2e26;--line:#d6cfc0}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.65 Georgia,serif}header,main,footer{max-width:1000px;margin:auto;padding:32px 24px}header{padding-top:64px}h1{font-size:clamp(2.4rem,6vw,4rem);line-height:1.05;font-weight:normal;margin:20px 0}h2{font-size:2rem;line-height:1.2}h3{font-size:1.45rem}.eyebrow,.caption,summary,nav,.metrics{font-family:system-ui,sans-serif}.eyebrow{text-transform:uppercase;letter-spacing:.13em;font-size:.75rem;color:var(--accent)}.lead{max-width:780px;font-size:1.2rem}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}a{color:var(--accent)}nav a{padding:8px 14px;border:1px solid var(--line);border-radius:3px;text-decoration:none}section{border-top:2px solid var(--line);padding:36px 0 48px;scroll-margin-top:20px}.hebrew{font-size:1.8rem;line-height:1.9}.transliteration{font-style:italic}blockquote{border-left:3px solid var(--accent);margin:20px 0;padding:12px 22px;font-size:1.15rem}.caption{font-size:.8rem;color:#59616b}.metrics{display:flex;flex-wrap:wrap;gap:24px;font-size:.9rem}.metrics b{display:block;font-size:1.5rem}details{margin:22px 0;padding:16px;background:#fffcf5;border:1px solid var(--line);border-radius:4px}summary{cursor:pointer;font-size:1rem;color:var(--accent);font-weight:600}details[open] summary{margin-bottom:24px}.lesson p{max-width:78ch}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:.92rem;margin:20px 0}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}th{font-family:system-ui,sans-serif;font-size:.8rem}strong{color:#9d2922}.item{margin:5px 0}footer{border-top:1px solid var(--line);font-size:.9rem}@media print{details{border:0;padding:0}nav{display:none}body{background:white}}
.replay-status{border:2px solid var(--accent);padding:16px 22px;margin:24px 0;font-family:system-ui,sans-serif;font-size:1rem}.replay-status h2{font-size:1.2rem;margin:0}.replay-status p{margin:10px 0}.replay-status li{overflow-wrap:anywhere}
</style></head><body><header><div class="eyebrow">Quantum.Earth.Laing · Sherman G. Laing</div><h1>The Genesis Studies</h1>''' + status_html + '''
<p class="lead">Five expanded studies, preserved in full. Read the KJV, Hebrew, transliteration, gematria, New Testament witnesses, and exposition together.</p>
<p>This file works offline. Calculations and word counts were replayed from the included sources. Saved exposition is presented verbatim; original AI inference was not rerun.</p>
<nav>''' + "".join(navigation) + '''</nav></header><main>''' + "".join(sections) + '''</main><footer>
<p>Attribution: Sherman G. Laing / Quantum.Earth.Laing. See repository LICENSE.md for the noncommercial terms covering QEL material and third-party exceptions.</p>
<p>Display text, arithmetic, and interpretation are separate. Gematria totals do not validate theological claims. Original study Markdown and JSON remain the authoritative saved material.</p>
</footer></body></html>'''


def _build_replay(studies: Path, engine_path: Path, output: Path) -> dict:
    engine = load_engine(engine_path)
    baseline_path = studies / "QEL_Genesis_1_1_Study_20260910.json"
    if not baseline_path.is_file():
        raise ReplayError("Required recovered Genesis 1:1 baseline is missing")
    baseline_doc = read_document(baseline_path, "Genesis 1:1")
    baseline_markdown = baseline_path.with_suffix(".md").read_text(encoding="utf-8")
    baseline_count = len(baseline_doc["lesson_markdown"].split())
    baseline_result = study_replay(baseline_doc, baseline_markdown, baseline_path.name, engine, baseline_count)
    records, documents = [], []
    for verse in range(1, 6):
        path = studies / f"Genesis_1_{verse}_Expanded_Study.json"
        document = read_document(path, f"Genesis 1:{verse}")
        markdown = path.with_suffix(".md").read_text(encoding="utf-8")
        records.append(study_replay(document, markdown, path.name, engine, baseline_count))
        documents.append((document, markdown))
    results = {
        "schema": "qel-bible-offline-replay/1", "adapter_created": "2026-09-17",
        "owner": "Sherman G. Laing", "project": "Quantum.Earth.Laing",
        "status": "PASS" if baseline_result["state"] == "PASS" and all(r["state"] == "PASS" for r in records) else "FAIL",
        "engine": {"file": engine_path.name, "status": "recovered earlier clean-room WORD_CORE reference v2; not missing historical v1",
                   "source_unchanged_by_adapter": True},
        "execution": {"network_required": False, "model_inference": False,
                      "new_hashes_or_signatures": False, "new_greek_numeric_profile": True},
        "identities_note": "Source/transform/profile strings are descriptive labels, not cryptographic identities or owner signatures",
        "normalization": {"display": "Saved bytes; no display normalization",
                          "hebrew_calculation": "Recovered engine NFD; Hebrew combining marks removed; punctuation removed; whitespace collapsed",
                          "nfc_policy": "Canonically equivalent NFC and NFD input must yield the same consonantal result",
                          "maqaf": "Split for lexical source comparisons; join replayed separately to verify total invariance",
                          "final_letters": "Standard/ordinal/reduced use ordinary base letters; Gadol uses 500,600,700,800,900",
                          "reduced": "Sum of each ordinary letter value's digital root; not digital root of the full verse",
                          "input_guard": "New wrapper rejects foreign letters, numbers, controls, non-Hebrew combining marks, and symbols in Hebrew input"},
        "baseline": baseline_result, "studies": records,
    }
    comparisons = sum(len(row["checks"]) for row in [baseline_result, *records])
    if comparisons != 113:
        raise ReplayError(f"Replay profile requires 113 source comparisons; received {comparisons}")
    rendered_index = render_index(results, documents)
    lines = ["# Offline replay report", "", f"Overall state: **{results['status']}**.", "",
             "This new adapter replays saved study text, Hebrew arithmetic, selected Greek words and word counts. It does not rerun historical AI inference or create a signature.", "",
             "| Study | Lesson words | Standard | Gadol | Ordinal | Reduced | Greek | State |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for result in records:
        lanes = result["calculation"]["hebrew_lanes"]
        lines.append("| " + " | ".join(map(str, [result["passage"], result["word_counts"]["lesson_words"],
                     *[lanes[s]["total"] for s in SCHEMES], result["calculation"]["selected_greek"]["total"], result["state"]])) + " |")
    lines += ["", f"Recovered Genesis 1:1 baseline: {baseline_count:,} lesson words. Genesis 1:1 expanded: {records[0]['word_counts']['lesson_words']:,}; exact ratio {records[0]['word_counts']['ratio_to_genesis_1_1_baseline']}.",
              "Other verses use the same expanded study format; an exact doubled count against a separate earlier version is not claimed.", "",
              "Full checks and per-letter traces: results.json. Offline reader: index.html. Historical preaching counts remain source-reported because the files do not define machine-readable preaching boundaries.", ""]
    # All rendering completes before any success artifacts are staged.
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "index.html").write_text(rendered_index, encoding="utf-8")
    (output / "REPLAY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return results



def replay(studies: Path, engine_path: Path, output: Path) -> dict:
    """Publish a complete generation; failed attempts cannot retain old PASS here.

    Directory renames are not a multi-path filesystem transaction. A crash can
    leave no current directory, an INCOMPLETE record or an orphaned staging
    directory. Those are deliberately not a successful current generation.
    Previous generations are preserved in uniquely named superseded siblings.
    """
    output = Path(output).absolute()
    studies, engine_path = Path(studies).resolve(), Path(engine_path).resolve()
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ReplayError("Output must be a real directory, not a symlink or file")
    output = output.resolve()
    if output == studies or output in studies.parents or studies in output.parents or output in engine_path.parents:
        raise ReplayError("Output must not overlap study sources or contain the engine")
    run_id = uuid.uuid4().hex
    with output_lock(output):
        prior = None
        if output.exists():
            prior = output.with_name("." + output.name + ".superseded-" + run_id)
            output.rename(prior)
        output.mkdir()
        initial = _status(run_id, "INCOMPLETE", "INCOMPLETE", previous_generation=str(prior) if prior else None)
        atomic_json(output / "run-status.json", initial)
        atomic_json(output / "results.json", initial)
        # A previous integration PASS cannot be inherited by a replay-only run.
        atomic_json(output / "verification.json", {**initial, "state": "NOT_RUN", "status": "NOT_RUN"})
        stage = Path(tempfile.mkdtemp(prefix="." + output.name + ".staging-", dir=output.parent))
        try:
            results = _build_replay(studies, engine_path, stage)
            complete = _status(run_id, "COMPLETE", results["status"], artifacts=["results.json", "index.html", "REPLAY_REPORT.md"])
            atomic_json(stage / "run-status.json", complete)
            atomic_json(stage / "verification.json", {**complete, "state": "NOT_RUN", "status": "NOT_RUN"})
            incomplete = output.with_name("." + output.name + ".incomplete-" + run_id)
            output.rename(incomplete)
            try:
                stage.rename(output)
            except Exception:
                incomplete.rename(output)
                raise
            # Only our own temporary attempt records; never delete prior output.
            try:
                shutil.rmtree(incomplete)
            except OSError:
                pass  # An inert incomplete sibling may remain; publication already succeeded.
            return results
        except Exception as error:
            failure = _status(run_id, "INCOMPLETE", "ERROR", error_type=type(error).__name__, error=str(error),
                              previous_generation=str(prior) if prior else None,
                              staging_directory=str(stage), success_artifacts_published=False)
            try:
                atomic_json(output / "run-status.json", failure)
                atomic_json(output / "results.json", failure)
                atomic_json(output / "verification.json", {**failure, "state": "NOT_RUN", "status": "NOT_RUN"})
            except OSError as recording_error:
                raise ReplayError(f"{error}; unable to finish failure record: {recording_error}. No current success is established.") from error
            raise ReplayError(f"{type(error).__name__}: {error}") from error

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studies", type=Path, default=HERE / "studies")
    parser.add_argument("--engine", type=Path, default=HERE / "original" / "word_core" / "qel_word_core_reference_v2.py")
    parser.add_argument("--output", type=Path, default=HERE / "replay-output")
    args = parser.parse_args()
    try:
        results = replay(args.studies, args.engine, args.output)
    except (OSError, ValueError, KeyError, TypeError, ImportError, SyntaxError) as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        return 2
    count = sum(len(r["checks"]) for r in [results["baseline"], *results["studies"]])
    print(f"{results['status']}: five expanded studies + baseline; {count} source comparisons; offline reader at {args.output / 'index.html'}")
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
