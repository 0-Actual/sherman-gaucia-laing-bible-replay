# QEL Creation Week — public reading adaptation

**Owner and commissioning researcher:** Sherman G. Laing  
**Project:** Quantum.Earth.Laing  
**Historical build timestamp:** 3 May 2026, 15:49:26 UTC  
**Public adaptation prepared:** 17 September 2026

Open `index.html` in a browser. The scripts and stylesheet are local; no server, installation, account or network connection is required. The page displays the existing 34 Classic World English Bible verses from Genesis 1:1 through Genesis 2:3, eight QMAP nodes, recorded word/event mappings, text search and local JSON export.

This is a clearly labeled adaptation of recovered source files from the existing Bible Math Merge web build. It is not a newly invented substitute for that historical work. Its entire `scripts/q6_data.js` payload is unchanged from the recovered text copy.

## Changes in this adaptation

The owner-directed September 20 correction edition derives alphabetic counts from the saved calculation text, excludes the three apostrophes, labels historical count discrepancies, and adds corrected count metadata to exports. Diagram dragging no longer triggers node selection on release. Read [CORRECTIONS.md](CORRECTIONS.md). The original payload remains unchanged. Actual-browser visual verification remains open; the 72-hour review is not recorded as completed.

- Audio creation and playback are disabled. The original audio implementation has not been approved for the current audio-envelope requirements, and its Stop behavior is not treated as reliable. Event data remains visible.
- Unavailable illustrative image dependencies are replaced by a text note. No historical image is fabricated.
- The node palette uses one blue color; pitch labels and numerical data are unchanged.
- The interface identifies the owner, original date and scope, and labels the English calculation lane explicitly.
- The local source files are arranged into their existing referenced folder structure.

The original files are preserved separately as historical sources, including their prior audio code. This reading edition is the intended web entry point.

## Meaning of the numbers

The historical web payload uses English letter-value/event mappings. For example, its Genesis 1:1 English calculation total is 430. This is separate from the recovered Hebrew WORD_CORE result of 2701 for the stated Hebrew consonantal text. These are different source surfaces and conventions, not competing measurements of one input.

The data is a historical research/visualization payload. Recorded pitch/event mappings are not physical measurements or evidence of a unique biblical musical interpretation. The original build expressly does not embed the official Hebrew Tanach XML corpus.

## Sources and rights

The biblical text in this payload is identified by the original build as Classic World English Bible. eBible.org dedicates that translation to the public domain; the translation's name is a trademark, and changed biblical wording should not be represented as the original translation. This adaptation leaves the recovered payload unchanged. See the [official Classic WEB notice](https://ebible.org/eng-web/copr.htm).

The repository's noncommercial terms apply to QEL-owned original code, annotations and arrangement only. They do not restrict the public-domain Bible text, facts or arithmetic conventions. No separate license is claimed for SBLGNT or other full corpora, which are not embedded here.

## Validation

The historical September 17 JavaScript syntax and bounded DOM/canvas checks are preserved in `VALIDATION.json`; that file does not certify this correction candidate. Current regression evidence is in `CORRECTION_VALIDATION.json`, with the executable suite at `../test_web.mjs`. The current suite checks all 34 displayed verse counts, corrected export metadata, original-data preservation, drag/click behavior, navigation, search and inert audio callbacks. These are Node VM functional checks, not browser visual inspection or real playback tests.

No new cryptographic fingerprint or owner signature was generated.
