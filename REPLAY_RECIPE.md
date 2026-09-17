# Replayable expanded Scripture study

**Prepared September 17, 2026.** This is a newly written recovery and replay specification for Sherman G. Laing’s Quantum.Earth.Laing Bible studies. It describes the workflow requested by Sherman and the conventions present in the recovered September 10–12 studies. It is not presented as a recovered historical program, an independently trained model, or an owner-signed release.

## Two kinds of replay

1. **Replay an existing study.** Load the preserved Markdown and JSON, display their complete text, recompute the declared counts and letter-value traces, and reproduce the accompanying study views. No language-model call is needed for this operation.
2. **Prepare a new expanded study.** Use the specification below to compose a new lesson from declared source texts. Save that new lesson under a new identity with its inputs and checks. A prompt alone cannot guarantee the exact wording of an earlier generative answer. New prose must not replace the recovered original.

The recovered collection supplies Genesis 1:1–1:5 plus the earlier Genesis 1:1 baseline. Broader Bible lookup or older Bible-AI services belong to their separately recovered source packages. A five-verse collection must not be described as a complete Bible corpus.

## Inputs to preserve

- Biblical reference and the exact Hebrew or Greek source text, source edition or file, and source status.
- Exact KJV passage text and the source against which it was checked. Keep quotations distinct from a literal reading aid or paraphrase.
- Transliteration with a stated convention and a word-aligned reading aid.
- Gematria scheme, character-value table, normalization rules, token-boundary rules, and full per-letter trace.
- New Testament witnesses with their references, exact selected quotations, and the interpretive relationship stated separately from the quotation.
- Prior lesson used as the word-count baseline, counting method, target length, and whether the target applies to the complete lesson or a designated section.
- Study instructions, date, project attribution, assistant role, source limitations, and the new artifact’s review results.

The original studies already disclose their source status. Genesis 1:1 and 1:2 say their KJV passages were transcribed and internally reviewed from model textual knowledge rather than collated with an external KJV corpus in those turns. Later studies preserve their own source notes. Retain those statements. New textual checks can be documented as later checks without changing what was originally done.

## Study order and separation

1. Present the verse reference, original-language text, and exact KJV text.
2. Present transliteration and lexical or grammatical reading aids. Identify uncertainty and avoid assigning a speculative meaning to a Hebrew or Greek word.
3. Show word and letter counts and the complete declared gematria calculation. Place this in a calculation section separate from Scripture.
4. Identify New Testament witnesses and quote their selected text with references. Explain each correlation in the exposition; do not rewrite an Old Testament word to make it contain an entire later doctrine.
5. Give the extended preaching and teaching portion. Keep interpretation, prayer, application, and other commentary within the designated preaching portion. Source and calculation notes remain clearly labeled technical notes.
6. Preserve study attribution, source notes, and validation outside the quoted Scripture. Do not inject the owner’s private life or unrelated project context into the teaching.

The studies are Christian exposition, not a computational model of God’s essence. Numerical totals are calculations under stated conventions; they do not independently establish a theological interpretation or predictive claim.

## Hebrew gematria convention

Use standard additive Hebrew letter values, as explicitly stored in each study’s JSON:

| Letters | Values in the same order |
| --- | --- |
| א ב ג ד ה ו ז ח ט | 1 2 3 4 5 6 7 8 9 |
| י כ ל מ נ ס ע פ צ | 10 20 30 40 50 60 70 80 90 |
| ק ר ש ת | 100 200 300 400 |
| ך ם ן ף ץ | 20 40 50 80 90 |

Keep the pointed source text unchanged for display. For calculations, remove vowel and cantillation marks and exclude spaces and punctuation. Final letters retain their ordinary values; they do not receive 500–900 values in this scheme. Recognize Hebrew maqqef as a lexical boundary for the word-count convention used here. Keep lexical word count separate from whitespace units in the pointed display.

Reject an unexpected alphabetic character from calculation rather than silently assigning a value. Report every letter’s contribution, each word subtotal, any declared clause subtotal, and the verse total. Compare the normalized pointed text with the stored consonantal text before accepting the trace.

| Verse | Lexical words | Consonantal letters | Declared Hebrew total |
| --- | ---: | ---: | ---: |
| Genesis 1:1 | 7 | 28 | 2,701 |
| Genesis 1:2 | 14 | 52 | 3,546 |
| Genesis 1:3 | 6 | 23 | 813 |
| Genesis 1:4 | 12 | 45 | 1,776 |
| Genesis 1:5 | 13 | 49 | 2,141 |

These are the expectations recorded in the recovered JSON. An independent replay should calculate them from the displayed letters and flag a mismatch rather than changing the source silently.

## Greek witnesses and isopsephy

Calculate only the exact Greek form shown. Normalize diacritical marks for the calculation while retaining the original display. Use standard Greek isopsephy and count final sigma as sigma, value 200. Keep a dictionary form separate from an inflected form found in a cited passage.

| Study | Selected Greek form | Declared total | Scope |
| --- | --- | ---: | --- |
| Genesis 1:1 | λόγος | 373 | Selected word associated with John 1:1 |
| Genesis 1:2 | πνεῦμα | 576 | Displayed dictionary form; reference is stated in its record |
| Genesis 1:3 | φῶς | 1,500 | Displayed word for light |
| Genesis 1:4 | καλόν | 171 | Displayed inflected form; καλός is separately recorded as 321 |
| Genesis 1:5 | ἡμέρα | 154 | Displayed form in the 1 Thessalonians 5:2 witness |

Do not describe a selected word’s value as the value of an entire verse. Each record supplies its per-letter trace and contextual note.

## Length and the doubled study

The historical count is the number of whitespace-separated tokens: `len(text.split())`. Preserve this definition so that another person can reproduce it. It counts headings and formatting tokens and is not a linguistic tokenizer.

The recovered Genesis 1:1 baseline contains **5,386** tokens; its expanded successor contains **10,772**. That is an exact **2×** comparison for the complete lesson. Later lessons continue the expanded style at approximately ten thousand lesson tokens each. A separate shorter baseline for each later verse has not been recovered; do not claim one existed or claim an unverified exact doubling.

For future lessons, record the actual chosen baseline and target before composing. If the request is a minimum length, verify that minimum. If the request is exactly twice a prior count, report the achieved count and ratio without disguising a shortfall. Additional words should deepen textual explanation, witnesses, and teaching rather than pad the lesson with repetition.

## Direct speech and accessible presentation

Preserve KJV wording and capitalization inside quotations. Keep narration distinct from direct speech by God or Jesus. The recovered studies use bold Markdown for selected direct speech; their source notes describe red and bold formatting in the original PDFs. A new renderer may apply red to the same marked speech and should retain a visible non-color distinction such as bold so that meaning does not depend on color alone. Do not mark ordinary narration or every apostolic statement as direct divine speech.

Keep Hebrew display direction correct. Provide transliteration alongside Hebrew for readers who need it. A local read-aloud feature should speak the complete selected lesson and retain start, pause, resume, and stop controls when that feature is available. Availability of a device voice is a runtime capability to check, not proof that a preserved audio recording exists.

## Reusable lesson request

> Prepare an expanded Christian study of [reference] under the direction of Sherman G. Laing, Quantum.Earth.Laing. Use the supplied original-language and KJV texts as separately labeled sources. Give the original text, transliteration, declared reading aids, full standard gematria trace with ordinary final-letter values, and New Testament witnesses with exact selected quotations and references. Keep calculation, Scripture, and interpretation distinct. Put preaching, prayer, application, and commentary within the preaching portion. Exclude unrelated personal context. Follow the supplied word-count baseline and declared target. Preserve the exact source wording and record source uncertainties. Mark direct quoted speech by God or Jesus distinctly from narration. Save the complete lesson, structured inputs and outputs, source notes, and measured checks. Do not invent a source, quotation, historical date, completed test, owner signature, or deterministic replay result.

This request is newly written replay guidance. The actual recovered full lessons remain the primary reproducible outputs.

## Acceptance record

The study should retain its input texts, measured counts, calculation traces, selected witnesses, attribution, and source status. A successful arithmetic replay establishes agreement with the stated letter-value convention. It does not by itself certify manuscript accuracy, translation accuracy, historical priority, or doctrinal conclusions. Keep those review questions separate and record any corrections as dated additions while preserving the original study.
