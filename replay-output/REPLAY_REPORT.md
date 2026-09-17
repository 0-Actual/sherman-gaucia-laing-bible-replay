# Offline replay report

Overall state: **PASS**.

This new adapter replays saved study text, Hebrew arithmetic, selected Greek words and word counts. It does not rerun historical AI inference or create a signature.

| Study | Lesson words | Standard | Gadol | Ordinal | Reduced | Greek | State |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Genesis 1:1 | 10772 | 2701 | 4631 | 298 | 82 | 373 | PASS |
| Genesis 1:2 | 10709 | 3546 | 6516 | 576 | 234 | 576 | PASS |
| Genesis 1:3 | 10392 | 813 | 1373 | 201 | 66 | 1500 | PASS |
| Genesis 1:4 | 10281 | 1776 | 4676 | 381 | 147 | 171 | PASS |
| Genesis 1:5 | 10192 | 2141 | 4301 | 485 | 152 | 154 | PASS |

Recovered Genesis 1:1 baseline: 5,386 lesson words. Genesis 1:1 expanded: 10,772; exact ratio 2.0.
Other verses use the same expanded study format; an exact doubled count against a separate earlier version is not claimed.

Full checks and per-letter traces: results.json. Offline reader: index.html. Historical preaching counts remain source-reported because the files do not define machine-readable preaching boundaries.
