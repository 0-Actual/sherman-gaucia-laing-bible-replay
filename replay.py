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
    calc = document.get("text_and_calculations", document.get("word_core"))
    if not isinstance(calc, dict):
        raise ReplayError(f"Missing calculation record in {filename}")
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
<blockquote>{html.escape(display["kjv"])}</blockquote><p class="caption">King James Version · saved source text</p>
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
</style></head><body><header><div class="eyebrow">Quantum.Earth.Laing · Sherman G. Laing</div><h1>The Genesis Studies</h1>
<p class="lead">Five expanded studies, preserved in full. Read the KJV, Hebrew, transliteration, gematria, New Testament witnesses, and exposition together.</p>
<p>This file works offline. Calculations and word counts were replayed from the included sources. Saved exposition is presented verbatim; original AI inference was not rerun.</p>
<nav>''' + "".join(navigation) + '''</nav></header><main>''' + "".join(sections) + '''</main><footer>
<p>Attribution: Sherman G. Laing / Quantum.Earth.Laing. See repository LICENSE.md for the noncommercial terms covering QEL material and third-party exceptions.</p>
<p>Display text, arithmetic, and interpretation are separate. Gematria totals do not validate theological claims. Original study Markdown and JSON remain the authoritative saved material.</p>
</footer></body></html>'''


def replay(studies: Path, engine_path: Path, output: Path) -> dict:
    engine = load_engine(engine_path)
    baseline_path = studies / "QEL_Genesis_1_1_Study_20260910.json"
    if not baseline_path.is_file():
        raise ReplayError("Required recovered Genesis 1:1 baseline is missing")
    baseline_doc = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_markdown = baseline_path.with_suffix(".md").read_text(encoding="utf-8")
    baseline_count = len(baseline_doc["lesson_markdown"].split())
    baseline_result = study_replay(baseline_doc, baseline_markdown, baseline_path.name, engine, baseline_count)
    records, documents = [], []
    for verse in range(1, 6):
        path = studies / f"Genesis_1_{verse}_Expanded_Study.json"
        document = json.loads(path.read_text(encoding="utf-8"))
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
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "index.html").write_text(render_index(results, documents), encoding="utf-8")
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
    (output / "REPLAY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studies", type=Path, default=HERE / "studies")
    parser.add_argument("--engine", type=Path, default=HERE / "original" / "word_core" / "qel_word_core_reference_v2.py")
    parser.add_argument("--output", type=Path, default=HERE / "replay-output")
    args = parser.parse_args()
    try:
        results = replay(args.studies, args.engine, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        return 2
    count = sum(len(r["checks"]) for r in [results["baseline"], *results["studies"]])
    print(f"{results['status']}: five expanded studies + baseline; {count} source comparisons; offline reader at {args.output / 'index.html'}")
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
