# Recovered WORD_CORE source and test scope

**Attribution:** Sherman G. Laing · Quantum.Earth.Laing.

The reference implementation, its complete 43-test source, known-answer data and forensic Audit 002A verifier were recovered from complete existing text artifacts. The implementation identifies itself as a clean-room forward reference, distinct from earlier historical source files. Recovery did not rewrite its algorithm.

All four recovered files match their source records' reported UTF-8 byte counts after restoration of the terminal newline. This is a text-recovery and size check; the original 19-member Bible ZIP could not be transferred, and its full contents have not been independently inspected.

Forty of the 43 original unit tests were executed successfully during this recovery. Three tests are retained but were not executed because they compute historical SHA-256 values: 034, 038 and 041. The full forensic verifier is preserved as historical source and was not run because it generates such values throughout. Use the publication's current replay entry point for the no-new-hashes workflow; running the historical test script directly would run its old hash tests.

The current result is recorded in `RECOVERY_TEST_RESULTS.json`. It does not claim that all 100 historical forensic checks or all 16,079 historical comparisons were freshly rerun.

The implementation supports Hebrew standard, Gadol, ordinal and reduced-letter calculations and explicit maqaf handling. Its Greek function normalizes text only; it does not implement a Greek numerical profile. Source, transform and profile labels are caller declarations, not cryptographically authenticated identity. Wrapper validation may impose additional input constraints without changing the preserved source.

Only selected verse anchors are embedded in these source files. Complete SBLGNT, Hebrew Bible, full KJV, private conversation archives and original model weights are not included.

