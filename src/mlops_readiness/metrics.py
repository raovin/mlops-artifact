from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from mlops_readiness.cases import EvalCase
from mlops_readiness.providers import ModelProvider


@dataclass(frozen=True)
class EvalResult:
    id: str
    input: str
    output: str
    passed: bool
    reason: str
    tags: list[str]


def _check_expected(output: str, expected: dict[str, Any]) -> tuple[bool, str]:
    normalized_output = output.strip()
    if "exact" in expected:
        wanted = str(expected["exact"]).strip()
        if normalized_output != wanted:
            return False, f"expected exact '{wanted}', got '{normalized_output}'"
    for token in expected.get("contains", []):
        if str(token).lower() not in normalized_output.lower():
            return False, f"missing required text '{token}'"
    if "json_contains" in expected:
        try:
            parsed_output = json.loads(normalized_output)
        except json.JSONDecodeError as exc:
            return False, f"expected valid JSON output: {exc.msg}"
        passed, reason = _json_contains(parsed_output, expected["json_contains"])
        if not passed:
            return False, reason
    return True, "passed"


def _json_contains(actual: Any, expected: dict[str, Any], path: str = "$") -> tuple[bool, str]:
    if not isinstance(actual, dict):
        return False, f"expected JSON object at {path}"
    for key, expected_value in expected.items():
        child_path = f"{path}.{key}"
        if key not in actual:
            return False, f"missing JSON key {child_path}"
        actual_value = actual[key]
        if isinstance(expected_value, dict):
            passed, reason = _json_contains(actual_value, expected_value, path=child_path)
            if not passed:
                return False, reason
        elif actual_value != expected_value:
            return False, f"JSON value mismatch at {child_path}: expected {expected_value!r}, got {actual_value!r}"
    return True, "passed"


def evaluate_cases(cases: list[EvalCase], model: ModelProvider) -> list[EvalResult]:
    results: list[EvalResult] = []
    for case in cases:
        output = model.predict(case.input)
        passed, reason = _check_expected(output, case.expected)
        results.append(
            EvalResult(
                id=case.id,
                input=case.input,
                output=output,
                passed=passed,
                reason=reason,
                tags=case.tags,
            )
        )
    return results


def summarize_results(results: list[EvalResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = [result.id for result in results if not result.passed]
    by_tag: dict[str, dict[str, int]] = {}
    for result in results:
        for tag in result.tags or ["untagged"]:
            by_tag.setdefault(tag, {"total": 0, "passed": 0})
            by_tag[tag]["total"] += 1
            by_tag[tag]["passed"] += int(result.passed)
    for tag_summary in by_tag.values():
        tag_summary["failed"] = tag_summary["total"] - tag_summary["passed"]
        tag_summary["pass_rate"] = tag_summary["passed"] / tag_summary["total"] if tag_summary["total"] else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "failed_ids": failed,
        "by_tag": by_tag,
    }


def deployment_readiness(summary: dict[str, Any], min_pass_rate: float) -> dict[str, Any]:
    checks: list[str] = []
    if summary["total"] <= 0:
        checks.append("no eval cases found")
    if summary["pass_rate"] < min_pass_rate:
        checks.append(f"pass_rate {summary['pass_rate']:.3f} below threshold {min_pass_rate:.3f}")
    if summary["failed_ids"]:
        checks.append("failed cases: " + ", ".join(summary["failed_ids"]))
    return {
        "ready": not checks,
        "checks": checks or ["all checks passed"],
        "threshold": {"min_pass_rate": min_pass_rate},
    }


def results_as_dicts(results: list[EvalResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
