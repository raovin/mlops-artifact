from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: str
    expected: dict[str, Any]
    tags: list[str]


SUPPORTED_EXPECTATION_KEYS = {"contains", "exact", "json_contains"}


def _validate_expected(expected: dict[str, Any], case_id: str, line_number: int) -> None:
    unknown_keys = sorted(set(expected) - SUPPORTED_EXPECTATION_KEYS)
    if unknown_keys:
        raise ValueError(
            f"Case '{case_id}' line {line_number} has unsupported expectation key(s): "
            + ", ".join(unknown_keys)
        )
    if not expected:
        raise ValueError(f"Case '{case_id}' line {line_number} must define at least one expectation")
    if "contains" in expected:
        contains = expected["contains"]
        if not isinstance(contains, list) or not all(isinstance(token, str) for token in contains):
            raise ValueError(f"Case '{case_id}' line {line_number} contains must be a list of strings")
    if "exact" in expected and not isinstance(expected["exact"], str):
        raise ValueError(f"Case '{case_id}' line {line_number} exact must be a string")
    if "json_contains" in expected and not isinstance(expected["json_contains"], dict):
        raise ValueError(f"Case '{case_id}' line {line_number} json_contains must be an object")


def load_cases(path: Path) -> list[EvalCase]:
    """Load deterministic JSONL eval cases.

    Each line must contain:
    - id: stable case identifier
    - input: prompt/request to send to the model/provider
    - expected: assertion spec, currently supports contains, exact, and json_contains
    - tags: optional grouping labels
    """
    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            record = json.loads(stripped)
            try:
                case_id = str(record["id"])
                expected = dict(record["expected"])
                _validate_expected(expected, case_id=case_id, line_number=line_number)
                cases.append(
                    EvalCase(
                        id=case_id,
                        input=str(record["input"]),
                        expected=expected,
                        tags=list(record.get("tags", [])),
                    )
                )
            except KeyError as exc:
                raise ValueError(f"Missing required field {exc} on line {line_number}") from exc
    if not cases:
        raise ValueError(f"No eval cases found in {path}")
    return cases
