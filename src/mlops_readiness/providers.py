from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ModelProvider(Protocol):
    name: str

    def predict(self, text: str) -> str:
        """Return a model/API response for an input text."""


@dataclass
class RuleBasedModel:
    """Deterministic local stand-in for an LLM/API model.

    This keeps the scaffold runnable without secrets or paid APIs while preserving
    the same provider interface a real API client would implement.
    """

    name: str = "rule-based"

    def predict(self, text: str) -> str:
        normalized = text.lower()
        if "password" in normalized:
            return "To reset your password, open account settings, choose password reset, and verify your email."
        if "refund" in normalized:
            return "Refund requests should include order id, purchase date, and reason for the refund."
        if "summarize" in normalized or "summary" in normalized:
            return "Summary: The release improves evaluation coverage, deployment checks, and incident visibility."
        if "classify" in normalized and "urgent" in normalized:
            return "priority: high"
        if "json" in normalized:
            return '{"status":"ok","ready":true}'
        return "I do not have enough information to answer confidently."


@dataclass
class EchoModel:
    """Intentionally weak baseline useful for seeing failed checks."""

    name: str = "echo"

    def predict(self, text: str) -> str:
        return text


def get_model(name: str) -> ModelProvider:
    if name == "rule-based":
        return RuleBasedModel()
    if name == "echo":
        return EchoModel()
    raise ValueError(f"Unknown model '{name}'. Available: rule-based, echo")
