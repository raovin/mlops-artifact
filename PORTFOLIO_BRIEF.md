# Portfolio Brief: Deterministic MLOps Readiness Gate

## What this proves

This artifact shows how QA automation practices transfer directly into MLOps:

- acceptance criteria become versioned eval cases
- model/API responses are exercised through a provider boundary
- deterministic assertions convert qualitative behavior into release evidence
- structured JSON checks validate machine-readable response contracts
- pass-rate thresholds produce CI-friendly exit codes
- JSON reports preserve audit/debug context for reviewers and pipelines

## Why it is intentionally small

The goal is not to claim model quality from five toy examples. The goal is to show the operational shape of an evaluation gate that can run anywhere without credentials, hosted infrastructure, remote services, or large model downloads.

A real deployment would keep this skeleton and replace or extend:

1. provider adapter: local model, OpenAI-compatible endpoint, or internal inference service
2. eval data: larger representative case set with risk tags
3. metrics: schema checks, latency budgets, regression comparison, safety checks
4. reporting: trend storage, dashboards, or CI artifacts

## Reviewer commands

```bash
make test
make eval
make eval-fail
make verify
```

Expected behavior:

- `make test` passes the unit test suite
- `make eval` exits 0 and writes `reports/readiness-report.json`
- `make eval-fail` confirms the weak baseline is blocked with exit 1
- `make verify` runs the complete offline reviewer path

## Interview narrative

"I built this as a QA-to-MLOps bridge. Instead of treating model behavior as subjective, the harness makes it testable: eval cases are versioned, providers are swappable, assertions include text and structured JSON contracts, thresholds gate deployment, and every run emits JSON evidence. The included provider is intentionally local and dependency-free so the artifact is reproducible in CI and safe to review without secrets."
