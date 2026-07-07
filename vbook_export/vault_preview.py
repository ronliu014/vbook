"""Preview export for enhancing existing vault notes with vBook evidence."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PreviewSources:
    vault_note_path: Path
    lesson_output_dir: Path
    vault_note_markdown: str
    manifest: dict[str, Any]
    vision: dict[str, Any]
    sections: dict[str, Any]


@dataclass(frozen=True)
class PreviewPackage:
    preview_dir: Path
    enhancement_path: Path
    manifest_path: Path
    image_paths: list[Path]


def load_preview_sources(
    vault_note_path: Path | str,
    lesson_output_dir: Path | str,
) -> PreviewSources:
    note_path = Path(vault_note_path)
    output_dir = Path(lesson_output_dir)
    if not note_path.is_file():
        raise ValueError(f"vault note does not exist: {note_path}")
    manifest = _read_json(output_dir / "manifest.json")
    vision = _read_json(output_dir / "vision" / "analysis.json")
    sections = _read_json(output_dir / "fusion" / "sections.json")
    return PreviewSources(
        vault_note_path=note_path,
        lesson_output_dir=output_dir,
        vault_note_markdown=note_path.read_text(encoding="utf-8"),
        manifest=manifest,
        vision=vision,
        sections=sections,
    )


def render_enhancement_markdown(
    sources: PreviewSources,
    image_prefix: str = "images",
) -> str:
    lines = [
        sources.vault_note_markdown.rstrip(),
        "",
        "---",
        "",
        "## vBook 图文增强预览",
        "",
        "> 当前文件是预览，不会写回 vault。",
        "",
        f"- 原笔记：{sources.vault_note_path}",
        f"- vBook 输出：{sources.lesson_output_dir}",
        f"- 视觉分析：{sources.vision.get('analysis_count', 0)} 帧",
        "",
    ]
    analyses_by_image = _analyses_by_image_path(sources.vision)
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        lines.extend(_render_section(section, analyses_by_image, image_prefix))
    return "\n".join(lines).rstrip() + "\n"


def write_preview_package(
    sources: PreviewSources,
    preview_dir: Path | str,
) -> PreviewPackage:
    target_dir = Path(preview_dir)
    images_dir = target_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    copied_images = _copy_referenced_images(sources, images_dir)
    enhancement = render_enhancement_markdown(sources, image_prefix="images")
    enhancement_path = target_dir / "enhancement.md"
    enhancement_path.write_text(enhancement, encoding="utf-8")
    manifest_path = target_dir / "manifest.json"
    manifest = {
        "schema_version": "1",
        "status": "preview",
        "vault_note": str(sources.vault_note_path),
        "lesson_output_dir": str(sources.lesson_output_dir),
        "outputs": {
            "enhancement_md": "enhancement.md",
            "images_dir": "images",
        },
        "image_count": len(copied_images),
        "images": [str(path.relative_to(target_dir)) for path in copied_images],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return PreviewPackage(
        preview_dir=target_dir,
        enhancement_path=enhancement_path,
        manifest_path=manifest_path,
        image_paths=copied_images,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required artifact does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"artifact must be a JSON object: {path}")
    return data


def _render_section(
    section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
    image_prefix: str,
) -> list[str]:
    title = str(section.get("title") or "未命名知识点")
    summary = str(section.get("summary") or "")
    lines = ["### " + title, "", summary, ""]
    key_points = section.get("key_points")
    if isinstance(key_points, list) and key_points:
        lines.extend(["**关键要点**", ""])
        lines.extend(f"- {point}" for point in key_points if isinstance(point, str))
        lines.append("")
    image_refs = section.get("image_refs")
    if isinstance(image_refs, list) and image_refs:
        lines.extend(["**图像证据**", ""])
        for ref in image_refs:
            if not isinstance(ref, str):
                continue
            image_name = Path(ref).name
            analysis = analyses_by_image.get(ref) or analyses_by_image.get(image_name)
            alt_text = _image_alt_text(ref, analysis)
            lines.append(f"![{alt_text}]({image_prefix}/{image_name})")
            if analysis:
                ocr = str(analysis.get("ocr_text") or "").strip()
                desc = str(analysis.get("vision_description") or "").strip()
                if ocr:
                    lines.append(f"- OCR：{ocr}")
                if desc:
                    lines.append(f"- 画面理解：{desc}")
        lines.append("")
    return lines


def _analyses_by_image_path(vision: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    analyses = vision.get("analyses")
    if not isinstance(analyses, list):
        return result
    for analysis in analyses:
        if not isinstance(analysis, dict):
            continue
        image_path = analysis.get("image_path")
        if isinstance(image_path, str) and image_path:
            result[image_path] = analysis
            result[Path(image_path).name] = analysis
    return result


def _image_alt_text(ref: str, analysis: dict[str, Any] | None) -> str:
    if analysis:
        frame_id = analysis.get("frame_id")
        if isinstance(frame_id, str) and frame_id.strip():
            return frame_id
    return Path(ref).stem


def _copy_referenced_images(sources: PreviewSources, images_dir: Path) -> list[Path]:
    copied: list[Path] = []
    seen: set[Path] = set()
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        image_refs = section.get("image_refs")
        if not isinstance(image_refs, list):
            continue
        for ref in image_refs:
            if not isinstance(ref, str):
                continue
            source = Path(ref)
            if not source.is_file() or source in seen:
                continue
            target = images_dir / source.name
            shutil.copy2(source, target)
            copied.append(target)
            seen.add(source)
    return copied
