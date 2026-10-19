# Architecture Notes

This project is a small MLOps release gate, not a model quality benchmark. It shows how a team can turn expected model/API behavior into repeatable checks that are safe to run in local development or CI.

## Flow

```text
JSONL eval cases
  -> provider adapter
  -> deterministic assertions
  -> pass-rate threshold
  -> JSON report
  -> CI exit code
```

## Boundaries

- `data/sample_cases.jsonl` stores versionable acceptance cases.
- `src/mlops_readiness/providers.py` isolates model/API behavior behind a `predict()` interface.
- `src/mlops_readiness/metrics.py` evaluates outputs with deterministic checks.
- `src/mlops_readiness/runner.py` owns CLI parsing, config loading, report rendering, and process exit status.
- `reports/readiness-report.json` is the machine-readable evidence artifact a pipeline can archive.

## Supported Checks

- `contains`: every listed string must appear in the output, case-insensitive.
- `exact`: the trimmed output must exactly match the expected string.
- `json_contains`: the output must be valid JSON and include the expected object keys and values. Extra output keys are allowed so contracts can check stable fields without overfitting to metadata.

## Extension Points

Add a real provider without changing the harness:

1. Implement a new provider class with `name` and `predict(text: str) -> str`.
2. Register it in `get_model()`.
3. Add or update JSONL cases that represent the target workflow.
4. Run `make verify` before using the provider in CI.

Useful next checks for a production version:

- JSON schema validation for structured responses.
- Latency budgets and timeout handling.
- Regression comparison against a previous report.
- Risk-tier thresholds by tag, for example stricter gates for safety or incident cases.
- Redacted report mode for sensitive inputs and outputs.
