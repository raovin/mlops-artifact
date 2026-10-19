# MLOps Readiness Scaffold

[![tests](https://github.com/raovin/mlops-artifact/actions/workflows/tests.yml/badge.svg)](https://github.com/raovin/mlops-artifact/actions/workflows/tests.yml)

A small, practical QA-to-MLOps artifact: deterministic evaluation cases, a swappable model/provider boundary, deployment-readiness gating, JSON reporting, and CI-ready tests.

The scaffold is intentionally offline and dependency-light. It uses only the Python standard library by default: no paid APIs, no secrets, no network calls, and no large model downloads.

## Case study

A personal showcase project that maps QA automation patterns onto ML and data-system release checks. Write-up: [glyphknit.com/work/mlops-readiness-scaffold](https://glyphknit.com/work/mlops-readiness-scaffold/).

**Problem.** Model behavior can drift into subjective review. The useful engineering shape is a repeatable gate: versioned cases, provider boundaries, deterministic assertions, thresholds, and report evidence.

**Approach.** Expected behavior is written as JSONL eval cases. Outputs are routed through a swappable provider, checked against text (`contains`, `exact`) and structured JSON (`json_contains`) expectations, and summarized into a CI-friendly pass/fail readiness result with a JSON report.

**How the readiness gate works.**

1. `cases.py` loads and validates the JSONL cases; malformed expectations fail fast.
2. `providers.py` returns a model behind a `predict(text) -> str` boundary: a deterministic `rule-based` stand-in and an intentionally weak `echo` baseline.
3. `metrics.py` scores each case, rolls up pass rates per tag, and compares the overall pass rate with `--min-pass-rate`.
4. `runner.py` prints the JSON report (and writes it with `--output`, e.g. `reports/readiness-report.json`), then exits `0` when the gate passes or `1` when it is blocked.
5. `make eval-fail` runs the weak `echo` baseline and succeeds only if the gate blocks it with exit `1`, so CI proves the gate can fail, not just pass.

**Constraints.** No paid APIs, secrets, network calls, or model downloads; small enough for reviewers to run locally; clear extension points for real providers and stricter production gates.

**Limits.** The five sample cases demonstrate the release-gate shape. They are not a production model benchmark, and `rule-based` is a deterministic stand-in, not an LLM.

**Run it.**

```bash
make verify   # unit tests, passing gate, config-driven gate, blocked weak-baseline demo
```

CI ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) runs the same `make verify` on every push and pull request.

## Why this is useful

This project demonstrates how QA automation skills map directly to MLOps work:

- versioned acceptance/eval cases for model behavior
- deterministic checks for text and structured JSON outputs
- a model provider boundary that can be replaced by a real model or API
- deployment-readiness thresholds with CI-friendly exit codes
- machine-readable reports for debugging and audit evidence

## Project structure

```text
mlops-artifact/
├── .github/workflows/tests.yml       # CI example: offline verification
├── config/readiness.example.json     # repeatable eval run config
├── data/sample_cases.jsonl           # deterministic eval fixtures
├── docs/architecture.md              # concise architecture notes
├── docs/reviewer-checklist.md        # portfolio/reviewer checklist
├── reports/                          # generated and review reports
├── src/mlops_readiness/
│   ├── cases.py                      # JSONL eval case loading/validation
│   ├── metrics.py                    # assertions, summaries, readiness gate
│   ├── providers.py                  # local deterministic providers
│   └── runner.py                     # CLI runner
├── tests/test_eval_harness.py        # CI-ready unit tests
├── Makefile
├── PORTFOLIO_BRIEF.md
└── pyproject.toml
```

## Quick start

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run the passing readiness gate:

```bash
make eval
```

This writes `reports/readiness-report.json` and exits `0` when the readiness threshold is met.

Run all offline verification steps:

```bash
make verify
```

Expected behavior:

- unit tests pass
- `rule-based` provider passes the readiness gate
- config-driven eval works
- weak `echo` provider is blocked with exit `1` in the intentional failure demo

## Direct CLI usage

```bash
PYTHONPATH=src python -m mlops_readiness.runner \
  --cases data/sample_cases.jsonl \
  --model rule-based \
  --min-pass-rate 1.0 \
  --output reports/readiness-report.json
```

Run from config:

```bash
PYTHONPATH=src python -m mlops_readiness.runner --config config/readiness.example.json
```

Demonstrate a blocked gate:

```bash
PYTHONPATH=src python -m mlops_readiness.runner --model echo --min-pass-rate 0.8
```

## Tests

```bash
make test
# or
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Adapting to a real model or API

1. Add a provider in `src/mlops_readiness/providers.py` with a `predict(text: str) -> str` method and a `name`.
2. Register it in `get_model()`.
3. Add representative JSONL cases in `data/sample_cases.jsonl` or a new file.
4. Tune `--min-pass-rate` or `config/readiness.example.json` for your release gate.
5. Keep secrets out of the repo; use environment variables or CI secret stores for real endpoints.

## Portfolio next steps

- Add a screenshot/table comparing the passing provider with the blocked provider.
- Add a small local FastAPI inference endpoint and evaluate it through the same provider boundary.
- Add regression comparison against the previous JSON report to catch quality drift.
- Expand cases by risk area: support, privacy, JSON contracts, safety, and edge cases.
- Publish `PORTFOLIO_BRIEF.md` with the repo link and a short demo GIF.
