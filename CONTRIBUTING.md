# Contributing to Bible Replay

This public Bible build is attributed to **Sherman Gaucia Laing / Quantum.Earth.Laing**. Reproducible bug reports, research comparisons, documentation corrections, and proposed fixes are welcome.

Read [LICENSE.md](LICENSE.md), [ATTRIBUTION.md](ATTRIBUTION.md), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before contributing. Contributions intended for inclusion follow the license's contribution terms. Retain source attribution and applicable AI-assistance disclosures, identify your modifications, and disclose third-party material and its terms. Contributors retain ownership of their own protectable contributions. Commercial use of covered material requires Sherman's prior explicit written authorization; contributing does not grant that permission.

## Report a reproducible problem

Use the bug report template in [Issues](https://github.com/0-Actual/sherman-gaucia-laing-bible-replay/issues). Give the affected file and commit or version, operating system, Python version when relevant, exact steps, expected result, actual result, and the smallest relevant error excerpt. Link related reports. Include only information you intend to make public; private conversations, credentials, and unrelated laptop logs do not belong in a public report.

## Propose and verify a change

Make a focused change in a branch or fork and open a pull request explaining the problem, resulting behavior, and verification. Keep recovered originals and their provenance intact. Propose corrections transparently; do not silently rewrite historical sources, dates, or reported results. Label new adaptations as new work, and distinguish saved exposition from arithmetic checks.

From the repository folder with Python 3.10 or later:

```sh
python verify.py
```

On Windows, `py -3 verify.py` is an alternative when the Python launcher is installed. No extra Python packages or model services are needed. The command runs the saved-study replay, 15 adapter tests, and 40 selected recovered WORD_CORE tests. Its three archival test exclusions and historical-verifier behavior remain unchanged. Include the actual command result in the pull request; if it was not run, say so.

[Bible replay checks](https://github.com/0-Actual/sherman-gaucia-laing-bible-replay/actions/workflows/replay-checks.yml) runs the same command on standard GitHub-hosted Ubuntu and Windows machines with Python 3.12. Each run reports its own result. Checks do not merge changes or publish a release. The wider private QEL development archive is outside this repository's contribution scope.
