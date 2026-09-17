# Replay the Bible studies offline

This adapter was newly written on September 17, 2026 for Sherman G. Laing / Quantum.Earth.Laing. It calls the recovered earlier `qel_word_core_reference_v2.py` without changing that file. That earlier engine identifies itself as a clean-room reference, not the missing historical version 1 source. The adapter is not presented as an original early AI service.

Run from the repository with Python 3.10 or later:

```sh
python replay.py
```

On Windows, use `py -3 replay.py` if Python is installed under the Python launcher. There are no package installations, API keys, model services or network requests. The input files are `studies/Genesis_1_{1..5}_Expanded_Study.{json,md}` and `studies/QEL_Genesis_1_1_Study_20260910.{json,md}`. The engine is `original/word_core/qel_word_core_reference_v2.py`. Missing inputs fail with a nonzero exit status.

The command writes `replay-output/results.json`, `replay-output/REPLAY_REPORT.md`, and `replay-output/index.html`. Open the HTML file directly to read all five complete expanded studies. The reader is self-contained, has no scripts, requests or remote assets, and blocks network connections through its content security policy. If Python is unavailable, the included generated reader still opens as a local file. Rerunning writes derived outputs only; it does not edit the recovered studies or engine.

The replay command returns 0 only if all source comparisons pass; 1 means a comparison failed; 2 means the replay could not complete. The command prints the comparison count. Inspect the current terminal result when rerunning; previously generated output is not proof that a later interrupted or failed run passed.

To run the new adapter tests:

```sh
python test_replay.py
```

Tests use saved known-answer fixtures, malformed-input cases, a deliberately changed expected total, changed word counts, and byte-for-byte comparison of repeated derived output. Historical hash tests are not imported or run. Engine and study paths can be overridden with `--engine PATH` and `--studies PATH`; the replay output location can be changed with `--output PATH`.

## What is replayed

- The saved KJV text, Hebrew presentation, transliteration, New Testament witnesses, and complete exposition are reused without requesting fresh model output.
- Hebrew is recalculated using four separately named conventions: Standard, Gadol, ordinal and reduced. Standard per-word and per-letter traces, recorded clause subtotals, and the stated factor product are checked against the saved study JSON. Clause boundaries follow the arithmetic paragraphs in the saved studies. The recorded Genesis 1:4 second-clause comparison with Genesis 1:3 is also recalculated.
- The selected Greek words are recomputed with a **new, limited reference profile**, using the letter values written in the recovered study traces. A historical draft Greek map is recovered separately, but it has `allow_execution: false` and an unset primary-text identity; this adapter does not activate it or claim a frozen historical Greek corpus replay. The retained engine supplies normalization, not this numeric map. Unlisted Greek letters are rejected.
- Unicode and maqaf behavior are checked. NFC and NFD equivalents must give the same consonantal result. Maqaf is split for the saved lexical word counts and separately joined to verify total invariance.
- The saved lesson's whitespace tokens are counted with `len(text.split())`. This is a reproducible token count, not a linguistic word tokenizer. Markdown files and JSON lesson bodies are counted separately where Markdown includes additional notes.
- Genesis 1:1's baseline has 5,386 tokens and its expanded lesson has 10,772: exactly double. Other verses follow the expanded study format; no separate earlier baseline or exact twofold increase is invented for them.

Historical preaching counts are retained as source-reported values because no explicit machine-readable boundary for the preaching portion is included. The replay validates the complete saved lesson counts.

## Text, calculation, interpretation

The result records these separately. The display surface is retained as saved. The recovered engine uses canonical decomposition (NFD), removes Hebrew combining marks, removes punctuation, collapses whitespace, and treats maqaf according to the selected mode. This new adapter adds a strict input boundary to reject foreign letters, digits, controls, symbols and non-Hebrew combining marks before calling the engine. This prevents silent loss of unsupported semantic characters without modifying the recovered engine.

Standard uses ordinary final-letter values. Gadol uses final kaf/mem/nun/pe/tsadi values 500/600/700/800/900. Ordinal uses the 22 ordinary-letter positions, including ordinary positions for finals. Reduced sums the digital root of each ordinary letter value. It is not the digital root of the completed verse total. The five-final-letter fixture consequently has Standard 280, Gadol 3,500, ordinal 73 (11 + 13 + 14 + 17 + 18) and reduced 28.

Greek selected-word normalization uses the recovered engine's NFD mark removal, lowercase conversion and final-sigma folding. The adapter supports only the numeric letters required by the recovered selected-word traces. This narrow implementation is explicitly new. Neither that arithmetic nor the Hebrew arithmetic establishes a theological conclusion.

The reader's formatting is a local presentation of the saved Markdown. Bold emphasis is rendered in red as a reading aid; the saved study text describes when that emphasis identifies direct words of God. The adapter does not infer divine speech from numbers or model output. Original Markdown and JSON are available for examining exact source text.

## Limits and provenance

This is deterministic replay of saved artifacts and declared arithmetic. It is not replay of historical model inference, hidden prompts, model weights, training, tool calls or unavailable services. A model can produce different prose on another run; this adapter reuses the actual saved study instead.

`source_id`, `transform_id` and `profile_id` are descriptive labels required by the recovered engine. They are not generated cryptographic identities, SGL Prime signatures, or proof of ownership. No new hashes or signatures are produced. Existing historical integrity material in separately retained original files is not executed by this adapter.

The exact displayed spelling governs arithmetic. Alternate spellings and alternate manuscripts can yield different totals. The included tests establish results for the supplied text and conventions only. Attribution, license, provenance, and the separately recorded publication state belong to the repository's documentation.
