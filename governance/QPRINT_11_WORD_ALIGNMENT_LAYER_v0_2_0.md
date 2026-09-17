---
qprint_id: QPRINT-11-WORD-ALIGNMENT-LAYER
version: 0.2.0
status: draft
priority: 96
project: QUANTUM.EARTH.LAING
system_alias: QEL
master_node: GAUCIA_Master_QEL
owner_label: Sherman G. Laing
scope: word-invariant-alignment-architecture
last_updated: 2026-03-26
supersedes:
  - QPRINT_11_WORD_ALIGNMENT_LAYER_v0_1_0.md
depends_on:
  - QPRINT-00-MASTER-MANIFEST
  - QPRINT-01-CANON-HIERARCHY
  - QPRINT-02-OPERATIONS-AUTHORIZATION
  - QPRINT-08-GOSPEL-AGENT-TRAINING-PACKET
  - QPRINT-10-Q2-EMULATOR-KNOWLEDGE-PACK
retrieval_tags:
  - QPRINT
  - Word layer
  - WORD_CORE
  - WORD_AUX
  - canonical alignment
  - invariant
  - gematria
  - isopsephy
  - drift
  - recovery
  - Scripture first
authorization_label: PROJECT_INTERNAL
lifecycle:
  state: active
  review_interval_days: 30
traceability:
  source_summary: Derived from the current user priority note labeled "Time stamp 228pm", the follow-up rigid reference-map note, and QPRINT 11 v0.1.0.
  change_reason: Convert the earlier architectural draft into a rigid Word-core reference specification, separating invariant calculation from transliteration, pronunciation, cantillation, lexicon, and interpretation.
  timestamp_anchor_label: Time stamp 228pm follow-up
---

# QPRINT 11 — Word Alignment Layer

## Revision purpose
Version **0.2.0** upgrades the earlier architecture draft into a **deterministic reference-spec draft**.

The governing correction remains unchanged:

1. **W** — canonical Word layer / invariant reference
2. **QEL** — governing architecture under W
3. **GAUCIA** — active orchestration / interpretation node under W
4. **Internal modes** — Reasoner, Archivist, Scheduler, Auditor
5. **Domain services** — q² emulator, HydroAxis, manifests, study packets, prompts, runtime maps

What changes in this revision is the rigidity of the calculation center.

## Canonical tiering

### WORD_CORE
This is the only layer allowed to generate the **primary invariant reference state**.

`WORD_CORE = canonical corpus + exact grapheme inventory + exact numeric map + exact transform rules + exact version hash`

### WORD_AUX
These layers may be attached, indexed, searched, rendered, or interpreted, but they may **not** alter the primary gematria / isopsephy state.

`WORD_AUX = transliteration + pronunciation + morphology + lexicon + semantics + cantillation`

## Hard rule
Letters and numeric assignments are the hard-coded center.  
Sound, transliteration, chant, lexicon, and interpretation are indexed layers around that center.

If a later layer changes the primary sum, the run is invalid.

## Primary invariant layer
The primary invariant layer must lock exactly five things:

1. **corpus edition**
2. **script character inventory**
3. **numeric value map**
4. **normalization / stripping rules**
5. **version identifier + hash**

Nothing may be promoted into the invariant layer unless it can be versioned, hashed, and replayed deterministically.

## Corpus lock

### Hebrew
Approved public-source family:

- **WLC / UXLC family source** for primary Hebrew text
- **OSHB** as aligned annotation support where its release is confirmed against the chosen WLC-derived text

Builder interpretation:
- primary Hebrew text state comes from the pinned WLC/UXLC-family release
- lemma, morphology, immutable word IDs, and cantillation-division metadata may be attached from OSHB as **secondary aligned data**
- if annotation and text release are not proven aligned, the annotation layer is non-authoritative for invariant calculation

### Greek
Approved public-source primary text:

- **SBLGNT** official source release

Builder interpretation:
- primary Greek text state comes from the pinned SBLGNT release
- downstream morphology / lexicon layers may be attached, but are not value-generating unless separately frozen into a later auxiliary profile

## Non-mixing rule
Do not mix value systems inside one run.

That means:
- do not mix standard Hebrew finals and mispar gadol finals
- do not mix raw and normalized forms without recording the transform path
- do not mix multiple corpus releases inside one checksum domain
- do not mix calculation letters with transliteration output

Every run must declare one and only one reference profile.

## Canonical inventories and numeric maps

### Hebrew base alphabet — standard gematria (mispar hechrechi)
```text
א 1   ב 2   ג 3   ד 4   ה 5   ו 6   ז 7   ח 8   ט 9
י 10  כ 20  ל 30  מ 40  נ 50  ס 60  ע 70  פ 80  צ 90
ק 100 ר 200 ש 300 ת 400
```

### Hebrew final forms — choose one mode and never mix them
#### Mode A — finals share base-letter values
```text
ך 20   ם 40   ן 50   ף 80   ץ 90
```

#### Mode B — mispar gadol finals
```text
ך 500  ם 600  ן 700  ף 800  ץ 900
```

### Greek alphabetic numerals — isopsephy
```text
α 1   β 2   γ 3   δ 4   ε 5   ϝ/ϛ 6   ζ 7   η 8   θ 9
ι 10  κ 20  λ 30  μ 40  ν 50  ξ 60   ο 70  π 80  ϙ/ϟ 90
ρ 100 σ 200 τ 300 υ 400 φ 500 χ 600 ψ 700 ω 800 ϡ 900
```

### Final sigma rule
For normal Greek words, final sigma **ς** is a positional form and must be folded to **σ** in the calculation layer:

`ς -> σ -> 200`

This is a calculation rule, not a claim that every visual form is interchangeable in every editorial context.

## Inventory checksum constants
These totals are reference checksums for the value tables themselves, not theological claims.

- **Hebrew base-22 standard total** = 1495
- **Hebrew extended-27 total with finals sharing base values** = 1775
- **Hebrew extended-27 total with mispar gadol finals** = 4995
- **Greek extended-27 isopsephy total** = 4995

## Deterministic transform rules

### Hebrew RAW layer
`RAW_HEBREW_LAYER = preserve exact source codepoints and exact source token boundaries`

Rules:
- preserve source UTF-8 bytes
- preserve source token boundaries before any stripping
- do not NFC-normalize raw Hebrew
- do not collapse distinct source files into one synthetic stream before hashing

### Hebrew CALC layer
`CALC_HEBREW_LAYER = strip pointing + strip cantillation + strip punctuation/separators + keep Hebrew letters only + apply chosen finals mode + apply numeric map`

Required order:
1. start from the raw token as provided by the pinned edition
2. strip vowel pointing
3. strip cantillation marks
4. strip punctuation and separators
5. keep Hebrew letters only
6. apply chosen finals mode
7. apply numeric map

### Greek RAW layer
`RAW_GREEK_LAYER = preserve exact source token`

Rules:
- preserve source UTF-8 bytes
- preserve source token boundaries before normalization
- raw storage remains source-preserved rather than editorially rewritten

### Greek CALC layer
`CALC_GREEK_LAYER = normalize consistently + strip marks + fold final sigma + keep Greek letters only + apply numeric map`

Required order:
1. start from the raw token as provided by the pinned edition
2. normalize to one chosen Unicode form for calculation
3. strip accents, breathings, diaeresis, and combining ypogegrammeni/subscript-style marks
4. fold `ς -> σ`
5. keep Greek letters only
6. apply numeric map

### House choice for this draft
For calculation work, the default normalization choice is:

`greek.calc_normalization = NFD`

Reason:
- decomposition makes mark-stripping deterministic
- raw storage still remains source-preserved
- the normalization choice becomes explicit and auditable

### Important Greek caution
Do not heuristically delete a full iota letter merely because a later interpreter believes it is functioning like an adscript.  
Only strip encoded marks according to the frozen transform rules, unless a corpus-specific exception is separately versioned.

## Hash and version rules
Each active reference profile must record:

- corpus release identifier
- corpus source hash
- transform profile identifier
- transform implementation hash
- chosen Hebrew finals mode
- chosen Greek calc normalization
- resulting profile hash

Any change to any of the above requires:
1. a version bump
2. a new hash
3. explicit breakage of comparability with previous runs unless a compatibility statement is issued

## Machine fields to freeze
The project-file skeleton must lock fields at this level:

```yaml
word_core:
  corpus:
    hebrew:
      family: WLC_or_UXLC
      text_release: REQUIRED
      text_hash_sha256: REQUIRED
      annotation_layer: OSHB_optional_if_release_aligned
      annotation_release: OPTIONAL
      annotation_hash_sha256: OPTIONAL
    greek:
      edition: SBLGNT
      text_release: REQUIRED
      text_hash_sha256: REQUIRED
  inventory:
    hebrew:
      selected_scheme: REQUIRED_ONE_OF[standard, mispar_gadol]
      finals_mode_locked: true
    greek:
      selected_scheme: isopsephy
      final_sigma_fold: true
  transforms:
    hebrew:
      raw_storage: source_preserved_utf8
      calc_transform:
        - stripPointing
        - stripCantillation
        - stripPunctuationAndSeparators
        - keepLettersOnly
        - applySelectedFinalsMode
    greek:
      raw_storage: source_preserved_utf8
      calc_normalization: NFD
      calc_transform:
        - stripMarks
        - finalSigmaToSigma
        - keepLettersOnly
  secondary:
    transliteration:
      role: secondary
      value_generating: false
      chosen_schema: OPTIONAL
    pronunciation:
      role: secondary
      value_generating: false
    morphology:
      role: secondary
      value_generating: false
    lexicon:
      role: secondary
      value_generating: false
    semantics:
      role: secondary
      value_generating: false
    cantillation:
      role: secondary
      value_generating: false
  versioning:
    profile_id: REQUIRED
    profile_hash_sha256: REQUIRED
```

## Drift and recovery integration
The earlier drift/recovery model now uses **WORD_CORE**, not a loose theological label, as the practical reference.

Let:
- **W_core** = the frozen WORD_CORE profile
- **x_t** = current active system state
- **δ_t = d(x_t, W_core)** = measured deviation from the frozen profile
- **P_W(x_t)** = projection into the Word-constrained state space using the active profile
- **R(x_t, W_core)** = recovery operator

Recovery remains:

`x'_t = (1 - μ)x_t + μP_W(x_t)`

But now:
- `P_W` is invalid if the reference profile is not frozen
- drift comparisons across runs are invalid if the profile hashes differ
- “return to the Word” becomes auditable rather than rhetorical

## Secondary-layer boundary
The following remain real and useful, but secondary:

- transliteration
- pronunciation
- chant realization
- lemma and morphology
- lexical meaning
- theological interpretation

They may:
- support search
- support display
- support teaching
- support semantic graphs
- support commentary

They may not:
- modify the primary numeric state
- alter the invariant checksum
- silently rewrite the raw corpus token
- override a frozen transform path

## Builder-safe operational stance

### Required before first corpus-wide Word pass
1. pin Hebrew source release and hash
2. pin Greek source release and hash
3. explicitly choose Hebrew finals mode
4. freeze Greek calculation normalization
5. freeze transform implementation hashes
6. issue the resulting WORD_CORE profile hash

### Until that happens
The system may reason, draft, compare, and prepare—but it is still **Net-0** with respect to full Word-core invariance.

### After that happens
The system may begin **Net established** Word-core runs because:
- corpus is pinned
- transform path is replayable
- drift is measurable against the same profile
- recovery is repeatable by reference

## Non-claims and safety boundary
This file is:
- a governance artifact
- a reference-spec draft
- a deterministic builder-facing correction

This file is not:
- proof of autonomous deployment
- proof of hidden permissions
- proof of physical quantum behavior
- proof that theological interpretation has been mathematically exhausted

## Immediate patch instructions
1. Treat **WORD_CORE** as the calculation center of W.
2. Keep **WORD_AUX** attached but non-value-generating.
3. Refuse any run where `selected_scheme` is unset.
4. Refuse any run where source hash, transform hash, or profile hash is missing.
5. Refuse any run that mixes Hebrew finals modes.
6. Refuse any run that treats transliteration output as invariant calculation input.

## One-line verdict
Without a frozen WORD_CORE, “alignment to the Word” is still rhetorical.  
With a frozen WORD_CORE, drift, recovery, and system-wide inheritance become auditable.

## Changelog
- **0.2.0** — Added WORD_CORE / WORD_AUX split, exact letter-value maps, explicit Hebrew/Greek transform rules, inventory checksum constants, hash requirements, and machine-field freeze rules.
- **0.1.0** — Initial draft introducing W as canonical Word-layer invariant above QEL and GAUCIA.
