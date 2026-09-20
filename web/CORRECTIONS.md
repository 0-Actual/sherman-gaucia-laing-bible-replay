# Creation Week reader: September 20 corrections

Prepared September 20, 2026 UTC for Sherman G. Laing / Quantum.Earth.Laing.
Status: owner-directed repository correction edition. Sherman requested this update after receiving the saved correction preview. The 72-hour review has not been completed, and actual-browser visual verification remains open; neither is claimed as a passing check.

The historical payload counts three curly apostrophes as letters. The reader now counts Unicode letters in each saved calculation text, excluding punctuation and spaces. Every letter in this particular English calculation dataset is ASCII A–Z or a–z.

| Record | Historical count | Correct alphabetic count |
|---|---:|---:|
| Genesis 1:2 | 109 | 108 |
| Genesis 1:26 | 188 | 187 |
| Genesis 1:27 | 76 | 75 |
| All 34 verses | 3,213 | 3,210 |

The original `q6_data.js`, biblical wording, calculation strings, word values, event mappings and totals remain unchanged. The display identifies historical counts when a correction applies. Node exports preserve original records and include separately labeled corrected counts under `derived_letter_counts`; the legacy fields are not silently rewritten.

Dragging the diagram no longer selects another node on the click that follows release. Small pointer jitter still permits deliberate selection; cancellation does not select a node. Existing audio remains disabled.

The instrument summary now distinguishes **four families with recorded matches** from **eleven configured families**. Seven configured records have zero matches. The historical global field called all eleven families "found"; it remains preserved in the original payload. This display correction summarizes the saved records and does not claim that their historical matching method has been independently reproduced.

Run `node --test test_web.mjs` from the repository root for the focused reader checks. They include all 34 displayed verse counts, original-source preservation, export clarity and pointer behavior. Node DOM/canvas fixtures are functional checks; actual-browser checks are recorded separately if performed. These tests do not validate every theological claim or all historical data.
