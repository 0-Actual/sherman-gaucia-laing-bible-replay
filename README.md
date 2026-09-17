# Sherman Gaucia Laing — Bible Replay

**Sherman Gaucia Laing / Quantum.Earth.Laing**  
Recovered Bible study services and clearly labeled new replay integration. Prepared September 17, 2026 with ChatGPT/GAUCIA and Codex assistance.

This repository contains the complete expanded Genesis 1:1–1:5 studies, the earlier Genesis 1:1 baseline, recovered WORD_CORE reference code and tests, Bible governance and agent instructions, a recovered web-source subset, and an offline replay process. It is prepared locally; the actual GitHub URL and publication time remain unset in [PUBLICATION_STATUS.json](PUBLICATION_STATUS.json).

## Read and explore

- Open [the complete offline study reader](replay-output/index.html). It includes all five expanded studies and the calculated summaries in one self-contained file. No installation or connection is required to read it.
- Open [the portable Creation Week interface](web/index.html) to explore the recovered 34-verse WEB dataset and its declared English-text numerical mappings. These mappings are distinct from Hebrew gematria. The portable edition removes unavailable images and historical sound generation.
- On Windows, `Open_Bible_Study.cmd` opens the complete reader after the repository folder has been extracted.
- Consult the [study catalog](STUDY_CATALOG.md), [service map](SERVICE_MAP.md), and [reusable study recipe](REPLAY_RECIPE.md).

The five expanded Markdown studies total **53,007 whitespace-separated tokens**. Genesis 1:1 grows from **5,386 to 10,772**, exactly double under the documented counting rule. Later studies preserve the expanded format; separate shorter baselines for those verses are not asserted.

## Replay and verify

With Python 3.10 or later, run from this folder:

```sh
python3 verify.py
```

On Windows with the Python launcher:

```bat
py -3 verify.py
```

`Replay_Bible.cmd` runs the same verification and keeps the result visible. Python must already be installed; the reader above works without Python.

The verification command runs the study replay, the new adapter tests and 40 selected recovered WORD_CORE tests. It requires no package download, model account, API key or network request. The original sources and studies are not rewritten. Derived results go to `replay-output/`.

The assembled preparation passed **113 replay comparisons**, **15 adapter tests** and **40 recovered WORD_CORE tests**. These are separate check sets, not a historical total. Inspect [the replay report](replay-output/REPLAY_REPORT.md) and [verification results](replay-output/verification.json). A later run's exit status determines that run's result; existing reports do not make a failed later run pass.

For command options and calculation conventions, read [REPLAY.md](REPLAY.md).

## What is preserved and what is new

| Path | Role |
| --- | --- |
| `studies/` | Complete recovered Markdown and JSON for five expanded studies and the baseline |
| `original/word_core/` | Recovered earlier clean-room WORD_CORE reference, known answers and historical tests |
| `governance/` | Recovered Bible governance, calibration and study-service instructions; identified public copies preserve their editing notes |
| `original/web/` | Recovered historical web-source subset; the old README may name unrecovered assets |
| `web/` | Explicitly labeled portable reading adaptation with original data preserved |
| `replay.py`, `test_replay.py`, `verify.py` | New September 17 integration and verification code |
| `replay-output/` | Reproducible derived report, complete reader and per-letter calculation results |

The earlier reference implementation is not the absent original version-one engine. Replaying saved study text and arithmetic does not rerun a past hosted AI model or reproduce its weights. Governance documents and calibration prompts preserve instructions; they are not a claim that a distinct model was trained. Read [HISTORICAL_SOURCE_NOTES.md](HISTORICAL_SOURCE_NOTES.md).

Three historical SHA-dependent tests and the old forensic verifier are preserved but not executed by the current verification command. No new owner signature or cryptographic fingerprint is produced. The original archives could not be downloaded; complete standalone text files supplied the recovered selection.

## Attribution and permissions

The selected Bible source and services are included under Sherman's current public-release direction. **Commercial use of covered material requires his prior explicit written authorization.** Read [LICENSE.md](LICENSE.md), [ATTRIBUTION.md](ATTRIBUTION.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The WEB Scripture text remains public domain and is not restricted by QEL's license. KJV study quotations retain their own source label.

The wider private QEL development archive and raw private conversations remain outside this release. The companion `sherman-gaucia-laing-research-record` repository contains the 175-entry chronology, evidence account and Sherman's statement about conducting most of his research with “Improve for all” shared data enabled. Its actual public URL will be recorded after successful publication.

Routine maintenance and responses are delegated within [MAINTENANCE.md](MAINTENANCE.md). Commercial permissions remain Sherman's decision. No live monitoring, public deployment or signed release is claimed before it is verified.
