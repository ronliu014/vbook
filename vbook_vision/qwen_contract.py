"""Shared classification helpers for normalized Qwen Vision results."""

from __future__ import annotations

from typing import Any


QWEN_RESULT_OK = "ok"
QWEN_RESULT_RECOVERED = "recovered"
QWEN_RESULT_DEGRADED = "degraded"
QWEN_RESULT_ERROR = "error"

MODEL_JSON_RECOVERY_WARNING = "model_json_recovery_retry"
DEGRADED_MODEL_WARNINGS = frozenset(
    {
        "degraded_empty_model_response",
        "degraded_malformed_model_response",
    }
)


def qwen_result_status(analysis: dict[str, Any] | None) -> str:
    """Classify a raw service response or normalized vBook analysis."""
    if not analysis:
        return QWEN_RESULT_OK
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        observations = {}

    services = [
        service
        for key in ("qwen_service", "qwen_service_response")
        if isinstance((service := observations.get(key)), dict)
    ]
    if any(service.get("status") == QWEN_RESULT_ERROR for service in services):
        return QWEN_RESULT_ERROR

    warnings = _warning_values(analysis.get("warnings"))
    for service in services:
        warnings.update(_warning_values(service.get("warnings")))

    if (
        observations.get("degraded") is True
        or any(service.get("status") == QWEN_RESULT_DEGRADED for service in services)
        or bool(warnings & DEGRADED_MODEL_WARNINGS)
    ):
        return QWEN_RESULT_DEGRADED
    if (
        MODEL_JSON_RECOVERY_WARNING in warnings
        or any(service.get("status") == QWEN_RESULT_RECOVERED for service in services)
    ):
        return QWEN_RESULT_RECOVERED
    return QWEN_RESULT_OK


def qwen_service_retryable(analysis: dict[str, Any] | None) -> bool | None:
    """Return the explicit service retry decision when one was recorded."""
    if not analysis:
        return None
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        return None
    for key in ("qwen_service", "qwen_service_response"):
        service = observations.get(key)
        if not isinstance(service, dict):
            continue
        retryable = service.get("service_retryable")
        if isinstance(retryable, bool):
            return retryable
    return None


def _warning_values(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}
