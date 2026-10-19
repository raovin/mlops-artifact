from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mlops_readiness.cases import load_cases
from mlops_readiness.metrics import (
    deployment_readiness,
    evaluate_cases,
    results_as_dicts,
    summarize_results,
)
from mlops_readiness.providers import get_model


DEFAULT_CASES = Path(__file__).parents[2] / "data" / "sample_cases.jsonl"
DEFAULT_MODEL = "rule-based"
DEFAULT_MIN_PASS_RATE = 0.8


def validate_min_pass_rate(value: float) -> float:
    """Return a valid readiness threshold in the inclusive range 0.0-1.0."""
    if not 0.0 <= value <= 1.0:
        raise ValueError("min_pass_rate must be between 0.0 and 1.0")
    return value


def load_run_config(path: Path) -> dict[str, Any]:
    """Load optional JSON run configuration for repeatable eval gates."""
    raw_config = json.loads(path.read_text(encoding="utf-8"))
    config: dict[str, Any] = {}
    if "cases" in raw_config:
        config["cases"] = Path(raw_config["cases"])
    if "model" in raw_config:
        config["model"] = str(raw_config["model"])
    if "min_pass_rate" in raw_config:
        config["min_pass_rate"] = validate_min_pass_rate(float(raw_config["min_pass_rate"]))
    if "output" in raw_config:
        config["output"] = Path(raw_config["output"])
    return config


def run_evaluation(cases_path: Path, model_name: str, min_pass_rate: float) -> dict[str, Any]:
    model = get_model(model_name)
    cases = load_cases(cases_path)
    results = evaluate_cases(cases, model)
    summary = summarize_results(results)
    readiness = deployment_readiness(summary, min_pass_rate=min_pass_rate)
    return {
        "metadata": {
            "tool": "mlops-readiness-scaffold",
            "schema_version": "1.0",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        },
        "model": model.name,
        "cases_path": str(cases_path),
        "summary": summary,
        "readiness": readiness,
        "results": results_as_dicts(results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic model output evals and deployment-readiness checks.")
    parser.add_argument("--config", type=Path, help="Optional JSON config with cases/model/min_pass_rate/output.")
    parser.add_argument("--cases", type=Path, help="Path to JSONL eval cases.")
    parser.add_argument("--model", choices=["rule-based", "echo"], help="Provider to evaluate.")
    parser.add_argument("--min-pass-rate", type=float, help="Minimum pass rate required for readiness.")
    parser.add_argument("--output", type=Path, help="Optional JSON report output path.")
    args = parser.parse_args()

    config = load_run_config(args.config) if args.config else {}
    cases_path = args.cases or config.get("cases", DEFAULT_CASES)
    model_name = args.model or config.get("model", DEFAULT_MODEL)
    min_pass_rate = (
        validate_min_pass_rate(args.min_pass_rate)
        if args.min_pass_rate is not None
        else config.get("min_pass_rate", DEFAULT_MIN_PASS_RATE)
    )
    output_path = args.output or config.get("output")

    report = run_evaluation(cases_path, model_name, min_pass_rate)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["readiness"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
