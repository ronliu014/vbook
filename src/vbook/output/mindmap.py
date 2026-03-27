# src/vbook/output/mindmap.py
from pathlib import Path
import json


def generate_markmap(analysis: dict) -> str:
    """Generate Markmap-compatible Markdown from analysis data."""
    lines = [f"# {analysis['title']}", ""]

    for section in analysis.get("outline", []):
        lines.append(f"## {section['title']}")
        lines.append(f"> {section['summary']}")
        lines.append("")

    if analysis.get("keywords"):
        lines.append("## 关键词")
        for kw in analysis["keywords"]:
            lines.append(f"- {kw}")
        lines.append("")

    return "\n".join(lines)
