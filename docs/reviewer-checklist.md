# Reviewer QA Checklist

Use this checklist to review the artifact as a QA-to-MLOps portfolio project. It is intentionally offline and dependency-free.

## Core Claim

This is not a model quality benchmark. It demonstrates the operational shape of an MLOps readiness gate:

- versioned eval cases
- swappable provider boundary
- deterministic output checks
- readiness threshold with non-zero failure exit
- JSON evidence suitable for CI artifacts

## Offline Verification

Run:

```bash
make verify
```

Expected result:

- unit tests pass
- passing rule-based eval exits `0`
- config-driven eval exits `0`
- weak `echo` baseline is blocked, and `make eval-fail` confirms the expected exit `1`

## Evidence To Inspect

- `data/sample_cases.jsonl`: small versioned case set covering support, policy, summarization, incident classification, and structured API output.
- `src/mlops_readiness/providers.py`: local provider boundary plus an intentionally weak baseline for failure demos.
- `src/mlops_readiness/metrics.py`: deterministic `contains`, `exact`, and `json_contains` checks with tag-level summaries.
- `reports/readiness-report.json`: machine-readable report with metadata, readiness status, summary, tag rollups, and per-case outcomes.
- `.github/workflows/tests.yml`: CI runs the same offline verification path a reviewer runs locally.

## Review Questions

- Can it run without secrets, network access, hosted services, Docker, or model downloads? Yes.
- Does a weak baseline fail the release gate? Yes, via `make eval-fail`.
- Are model/provider concerns isolated from evaluation logic? Yes, through the provider interface.
- Is the sample data large enough for model quality claims? No. It is a scaffold that demonstrates the release-gate pattern.

## Safe Extension Path

1. Add a real provider adapter behind `get_model()`.
2. Expand `data/sample_cases.jsonl` with representative cases and risk tags.
3. Add stricter checks such as JSON schema validation, latency budgets, regression deltas, and tag-specific thresholds.
4. Keep credentials outside the repo by reading from environment variables or a secret manager.
