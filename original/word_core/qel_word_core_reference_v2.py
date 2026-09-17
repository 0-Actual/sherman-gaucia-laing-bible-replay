"""Clean-room QEL WORD_CORE transform and Hebrew arithmetic reference.

Purpose
-------
This module independently implements the *documented* WORD_CORE rules used by
Project Quantum.Earth.Laing for forensic replay. It is not represented as the
original historical ``qel_gematria_core_v1.py`` or
``qel_word_core_transform_implementation_v1.py`` because those exact source
bytes were not mounted in the current runtime.

The implementation is intentionally fail-closed:
* source, transform, profile, language, and scheme identities are mandatory;
* transliteration/foreign alphabetic input is rejected;
* Hebrew standard and Gadol are separate calculation runs;
* maqaf handling is explicit;
* Unicode normalization is deterministic;
* WORD_AUX material is not accepted as invariant calculation input.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import unicodedata
from typing import Any, Iterable, Literal, Mapping


class WordCoreError(ValueError):
    """Fail-closed WORD_CORE validation error."""


HebrewScheme = Literal["standard", "gadol", "ordinal", "reduced"]
MaqafMode = Literal["join", "split"]
Language = Literal["hebrew", "greek"]


HEBREW_BASE_ORDER = "אבגדהוזחטיכלמנסעפצקרשת"
HEBREW_BASE_VALUES: dict[str, int] = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70,
    "פ": 80, "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}
HEBREW_FINAL_TO_BASE = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}
HEBREW_FINAL_GADOL = {"ך": 500, "ם": 600, "ן": 700, "ף": 800, "ץ": 900}
HEBREW_LETTERS = frozenset(HEBREW_BASE_VALUES) | frozenset(HEBREW_FINAL_TO_BASE)
HEBREW_ORDINAL = {letter: index for index, letter in enumerate(HEBREW_BASE_ORDER, 1)}
HEBREW_ORDINAL.update({final: HEBREW_ORDINAL[base] for final, base in HEBREW_FINAL_TO_BASE.items()})

# Common Greek letters accepted by the documented normalization lane.  This
# module verifies normalization only; it deliberately does not invent a Greek
# numeric profile absent the exact historical profile bytes.
GREEK_BASE_LETTERS = frozenset("αβγδεζηθικλμνξοπρστυφχψω")
GREEK_FINAL_SIGMA = "ς"
MAQAF = "\u05be"


@dataclass(frozen=True)
class IdentityBundle:
    source_id: str
    transform_id: str
    profile_id: str
    language: Language
    scheme: str

    def validate(self) -> None:
        for field_name in ("source_id", "transform_id", "profile_id", "language", "scheme"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise WordCoreError(f"missing required identity: {field_name}")
        if self.language not in {"hebrew", "greek"}:
            raise WordCoreError(f"unsupported language: {self.language!r}")
        if self.language == "hebrew" and self.scheme not in {"standard", "gadol", "ordinal", "reduced"}:
            raise WordCoreError(f"unsupported Hebrew scheme: {self.scheme!r}")
        if self.language == "greek" and self.scheme != "transform-only":
            raise WordCoreError("Greek numeric calculation is held until the exact numeric profile is materialized")


def _collapse_spaces(parts: Iterable[str]) -> str:
    return " ".join("".join(parts).split())


def _is_ignorable_punctuation(ch: str) -> bool:
    category = unicodedata.category(ch)
    return category.startswith("P") or category.startswith("Z")


def _reject_foreign_semantic_character(ch: str, language: str) -> None:
    category = unicodedata.category(ch)
    if category.startswith("L") or category.startswith("N"):
        raise WordCoreError(f"foreign/transliteration character rejected in {language} invariant lane: {ch!r}")
    if category.startswith("C") and ch not in {"\t", "\n", "\r"}:
        raise WordCoreError(f"control character rejected: U+{ord(ch):04X}")


def transform_hebrew(raw: str, *, maqaf_mode: MaqafMode) -> str:
    """Normalize pointed Hebrew to a letters-and-spaces calculation surface.

    * NFD makes canonically equivalent pointed forms deterministic.
    * Hebrew combining marks are removed.
    * ``maqaf_mode='join'`` removes maqaf without creating a boundary.
    * ``maqaf_mode='split'`` converts maqaf to a boundary.
    * Foreign letters and numbers fail closed instead of being silently lost.
    """
    if not isinstance(raw, str) or not raw:
        raise WordCoreError("Hebrew input must be a non-empty string")
    if maqaf_mode not in {"join", "split"}:
        raise WordCoreError(f"unsupported maqaf mode: {maqaf_mode!r}")

    out: list[str] = []
    for ch in unicodedata.normalize("NFD", raw):
        if ch in HEBREW_LETTERS:
            out.append(ch)
        elif ch == MAQAF:
            if maqaf_mode == "split":
                out.append(" ")
        elif ch.isspace():
            out.append(" ")
        elif unicodedata.category(ch).startswith("M"):
            # Hebrew vowel points and cantillation marks; NFD also separates
            # canonically equivalent marks before this rule.
            continue
        elif _is_ignorable_punctuation(ch):
            continue
        else:
            _reject_foreign_semantic_character(ch, "Hebrew")
    result = _collapse_spaces(out)
    if not result:
        raise WordCoreError("Hebrew transform produced an empty calculation surface")
    return result


def transform_greek(raw: str) -> str:
    """Documented Greek normalization reference, without a numeric map.

    The function lowercases, applies canonical decomposition, removes combining
    marks, folds final sigma to sigma, retains common Greek letters, and rejects
    foreign letters/numbers.
    """
    if not isinstance(raw, str) or not raw:
        raise WordCoreError("Greek input must be a non-empty string")
    out: list[str] = []
    # Decompose and remove marks *before* case folding.  This keeps the
    # declared mark-stripping lane from silently expanding an iota subscript
    # into a full iota (for example, ῇ -> η, not ηι).
    for ch in unicodedata.normalize("NFD", raw):
        if unicodedata.category(ch).startswith("M"):
            continue
        folded = ch.casefold()
        if folded == GREEK_FINAL_SIGMA:
            folded = "σ"
        if folded in GREEK_BASE_LETTERS:
            out.append(folded)
        elif ch.isspace():
            out.append(" ")
        elif _is_ignorable_punctuation(ch):
            continue
        else:
            _reject_foreign_semantic_character(ch, "Greek")
    result = _collapse_spaces(out)
    if not result:
        raise WordCoreError("Greek transform produced an empty calculation surface")
    return result


def digital_root(value: int) -> int:
    if not isinstance(value, int) or value < 0:
        raise WordCoreError("digital root requires a non-negative integer")
    if value == 0:
        return 0
    return 1 + (value - 1) % 9


def hebrew_value(letter: str, scheme: HebrewScheme) -> int:
    if letter not in HEBREW_LETTERS:
        raise WordCoreError(f"not a governed Hebrew letter: {letter!r}")
    base = HEBREW_FINAL_TO_BASE.get(letter, letter)
    if scheme == "standard":
        return HEBREW_BASE_VALUES[base]
    if scheme == "gadol":
        return HEBREW_FINAL_GADOL.get(letter, HEBREW_BASE_VALUES[base])
    if scheme == "ordinal":
        return HEBREW_ORDINAL[letter]
    if scheme == "reduced":
        return digital_root(HEBREW_BASE_VALUES[base])
    raise WordCoreError(f"unsupported Hebrew scheme: {scheme!r}")


def _validate_expected_identities(actual: IdentityBundle, expected: IdentityBundle | None) -> None:
    actual.validate()
    if expected is not None:
        expected.validate()
        if actual != expected:
            raise WordCoreError(
                "source/transform/profile/language/scheme identity mismatch: "
                f"actual={asdict(actual)!r}, expected={asdict(expected)!r}"
            )


def calculate_hebrew(
    raw: str,
    *,
    identities: IdentityBundle,
    maqaf_mode: MaqafMode = "join",
    expected_identities: IdentityBundle | None = None,
) -> dict[str, Any]:
    """Calculate exactly one explicitly named Hebrew scheme."""
    _validate_expected_identities(identities, expected_identities)
    if identities.language != "hebrew":
        raise WordCoreError("Hebrew calculation requires language='hebrew'")
    scheme: HebrewScheme = identities.scheme  # validated above
    surface = transform_hebrew(raw, maqaf_mode=maqaf_mode)
    words = surface.split()
    rows: list[dict[str, Any]] = []
    running_total = 0
    letter_count = 0
    for token in words:
        values = [hebrew_value(letter, scheme) for letter in token]
        subtotal = sum(values)
        running_total += subtotal
        letter_count += len(token)
        rows.append(
            {
                "token": token,
                "letters": list(token),
                "values": values,
                "subtotal": subtotal,
                "terminal_katan": digital_root(subtotal),
            }
        )
    return {
        "schema": "qel.word-core.reference-result/v2",
        "identities": asdict(identities),
        "maqaf_mode": maqaf_mode,
        "calculation_surface": surface,
        "word_count": len(words),
        "letter_count": letter_count,
        "total": running_total,
        "binary": format(running_total, "b"),
        "hex": format(running_total, "X"),
        "octal": format(running_total, "o"),
        "binary_round_trip": int(format(running_total, "b"), 2),
        "rows": rows,
    }


def calculate_named_hebrew_lanes(
    raw: str,
    *,
    source_id: str,
    transform_id: str,
    profile_id: str,
    maqaf_mode: MaqafMode = "join",
) -> dict[str, dict[str, Any]]:
    """Run each scheme independently and return separately named results."""
    return {
        scheme: calculate_hebrew(
            raw,
            identities=IdentityBundle(
                source_id=source_id,
                transform_id=transform_id,
                profile_id=profile_id,
                language="hebrew",
                scheme=scheme,
            ),
            maqaf_mode=maqaf_mode,
        )
        for scheme in ("standard", "gadol", "ordinal", "reduced")
    }


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Deterministic JSON for audit artifacts; no cryptographic authority."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
