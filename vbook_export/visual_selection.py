"""Shared scoring helpers for selecting useful course visuals."""

from __future__ import annotations

from typing import Any


_COMPLETION_MARKERS = (
    "完成态",
    "完整",
    "补全",
    "最终",
    "总结",
    "归纳",
    "清单",
    "要点",
    "定义",
    "区别",
    "位置",
    "操作",
    "结论",
    "框架",
)
_LOW_VALUE_MARKERS = (
    "过渡",
    "准备进入",
    "下一节",
    "刚开始",
    "只有标题",
    "空白",
    "切换",
    "封面",
)


def visual_value_key(
    analysis: dict[str, Any] | None,
    timestamp: float,
    fallback: str,
) -> tuple[int, float, int, int, int, float, str]:
    """Return a comparable key that prefers dense completed teaching pages."""
    ocr = _text_field(analysis, "ocr_text")
    description = _text_field(analysis, "vision_description")
    text = ocr + "\n" + description
    return (
        _marker_score(text),
        timestamp,
        _non_empty_line_count(ocr),
        len(ocr),
        _unique_non_space_char_count(ocr),
        visual_confidence(analysis),
        fallback,
    )


def visual_confidence(analysis: dict[str, Any] | None) -> float:
    if not analysis:
        return 0.0
    confidence = analysis.get("confidence")
    if isinstance(confidence, bool):
        return 0.0
    if isinstance(confidence, (int, float)):
        return float(confidence)
    return 0.0


def _text_field(analysis: dict[str, Any] | None, field: str) -> str:
    if not analysis:
        return ""
    return str(analysis.get(field) or "")


def _marker_score(text: str) -> int:
    return sum(text.count(marker) for marker in _COMPLETION_MARKERS) - sum(
        text.count(marker) for marker in _LOW_VALUE_MARKERS
    )


def _non_empty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _unique_non_space_char_count(text: str) -> int:
    return len({char for char in text if not char.isspace()})
