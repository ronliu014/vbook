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


@dataclass(frozen=True)
class PreviewScene:
    title: str
    start_timestamp: float | None
    end_timestamp: float | None
    sections: list[dict[str, Any]]
    image_refs: list[str]
    primary_image_ref: str | None
    key_points: list[str]
    summary: str


@dataclass(frozen=True)
class PreviewMetrics:
    scene_count: int
    rendered_primary_image_count: int
    omitted_repeated_image_count: int


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
    scenes = build_preview_scenes(sources, analyses_by_image)
    for scene in scenes:
        lines.extend(_render_scene(scene, analyses_by_image, image_prefix))
    return "\n".join(lines).rstrip() + "\n"


def write_preview_package(
    sources: PreviewSources,
    preview_dir: Path | str,
) -> PreviewPackage:
    target_dir = Path(preview_dir)
    images_dir = target_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    copied_images = _copy_referenced_images(sources, images_dir)
    metrics = preview_metrics(sources)
    enhancement = render_enhancement_markdown(sources, image_prefix="images")
    enhancement_path = target_dir / "enhancement.md"
    enhancement_path.write_text(enhancement, encoding="utf-8")
    manifest_path = target_dir / "manifest.json"
    manifest = {
        "schema_version": "1",
        "status": "preview",
        "vault_note": str(sources.vault_note_path),
        "lesson_output_dir": str(sources.lesson_output_dir),
        "source_vault_note": str(sources.vault_note_path),
        "workcopy_note": "enhancement.md",
        "safety": {
            "source_vault": "read_only",
        },
        "outputs": {
            "enhancement_md": "enhancement.md",
            "images_dir": "images",
        },
        "image_count": len(copied_images),
        "scene_count": metrics.scene_count,
        "rendered_primary_image_count": metrics.rendered_primary_image_count,
        "omitted_repeated_image_count": metrics.omitted_repeated_image_count,
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


def preview_metrics(sources: PreviewSources) -> PreviewMetrics:
    analyses_by_image = _analyses_by_image_path(sources.vision)
    scenes = build_preview_scenes(sources, analyses_by_image)
    rendered_primary_image_count = sum(1 for scene in scenes if scene.primary_image_ref)
    image_ref_count = sum(len(scene.image_refs) for scene in scenes)
    return PreviewMetrics(
        scene_count=len(scenes),
        rendered_primary_image_count=rendered_primary_image_count,
        omitted_repeated_image_count=max(
            0,
            image_ref_count - rendered_primary_image_count,
        ),
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required artifact does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"artifact must be a JSON object: {path}")
    return data


def build_preview_scenes(
    sources: PreviewSources,
    analyses_by_image: dict[str, dict[str, Any]] | None = None,
) -> list[PreviewScene]:
    analysis_lookup = analyses_by_image or _analyses_by_image_path(sources.vision)
    scenes: list[list[dict[str, Any]]] = []
    for section in sources.sections.get("sections", []):
        if not isinstance(section, dict):
            continue
        if scenes and _sections_belong_to_same_scene(
            scenes[-1][-1],
            section,
            analysis_lookup,
        ):
            scenes[-1].append(section)
        else:
            scenes.append([section])
    return [_preview_scene_from_sections(group, analysis_lookup) for group in scenes]


def _sections_belong_to_same_scene(
    current: dict[str, Any],
    next_section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
) -> bool:
    current_refs = set(_section_image_refs(current))
    next_refs = set(_section_image_refs(next_section))
    if current_refs.intersection(next_refs):
        return True
    current_topic = _section_visual_topic(current, analyses_by_image)
    next_topic = _section_visual_topic(next_section, analyses_by_image)
    if current_topic and current_topic == next_topic:
        return True
    return _normalized_title(current) == _normalized_title(next_section)


def _section_visual_topic(
    section: dict[str, Any],
    analyses_by_image: dict[str, dict[str, Any]],
) -> str:
    for ref in _section_image_refs(section):
        analysis = _analysis_for_ref(ref, analyses_by_image)
        if not analysis:
            continue
        observations = analysis.get("structured_observations")
        if not isinstance(observations, dict):
            continue
        topic = observations.get("topic")
        if isinstance(topic, str) and topic.strip():
            return " ".join(topic.split())
    return ""


def _normalized_title(section: dict[str, Any]) -> str:
    title = str(section.get("title") or "")
    return " ".join(title.split())


def _preview_scene_from_sections(
    sections: list[dict[str, Any]],
    analyses_by_image: dict[str, dict[str, Any]],
) -> PreviewScene:
    image_refs = _unique(
        ref for section in sections for ref in _section_image_refs(section)
    )
    primary_image_ref = _select_primary_image_ref(image_refs, analyses_by_image)
    title = _scene_title(sections)
    return PreviewScene(
        title=title,
        start_timestamp=_scene_start(sections),
        end_timestamp=_scene_end(sections),
        sections=sections,
        image_refs=image_refs,
        primary_image_ref=primary_image_ref,
        key_points=_scene_key_points(sections),
        summary=_scene_summary(sections),
    )


def _section_image_refs(section: dict[str, Any]) -> list[str]:
    image_refs = section.get("image_refs")
    if not isinstance(image_refs, list):
        return []
    return [ref for ref in image_refs if isinstance(ref, str) and ref.strip()]


def _scene_title(sections: list[dict[str, Any]]) -> str:
    for section in sections:
        title = str(section.get("title") or "").strip()
        if title:
            return title
    return "未命名知识点"


def _scene_summary(sections: list[dict[str, Any]]) -> str:
    summaries = []
    for section in sections:
        summary = str(section.get("summary") or "").strip()
        if summary:
            summaries.append(summary)
    return " ".join(_unique(summaries))


def _scene_key_points(sections: list[dict[str, Any]]) -> list[str]:
    points = []
    for section in sections:
        key_points = section.get("key_points")
        if not isinstance(key_points, list):
            continue
        points.extend(point for point in key_points if isinstance(point, str))
    return _unique(point.strip() for point in points if point.strip())


def _scene_start(sections: list[dict[str, Any]]) -> float | None:
    values = [
        _source_timestamp(section, 0)
        for section in sections
        if _source_timestamp(section, 0) is not None
    ]
    return min(values) if values else None


def _scene_end(sections: list[dict[str, Any]]) -> float | None:
    values = [
        _source_timestamp(section, 1)
        for section in sections
        if _source_timestamp(section, 1) is not None
    ]
    return max(values) if values else None


def _source_timestamp(section: dict[str, Any], index: int) -> float | None:
    timestamps = section.get("source_timestamps")
    if not isinstance(timestamps, list) or len(timestamps) <= index:
        return None
    value = timestamps[index]
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _select_primary_image_ref(
    image_refs: list[str],
    analyses_by_image: dict[str, dict[str, Any]],
) -> str | None:
    if not image_refs:
        return None
    successful = [
        ref
        for ref in image_refs
        if not _analysis_has_qwen_error(_analysis_for_ref(ref, analyses_by_image))
    ]
    candidates = successful or image_refs
    return max(candidates, key=lambda ref: _image_selection_key(ref, analyses_by_image))


def _analysis_for_ref(
    ref: str,
    analyses_by_image: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return analyses_by_image.get(ref) or analyses_by_image.get(Path(ref).name)


def _analysis_has_qwen_error(analysis: dict[str, Any] | None) -> bool:
    if not analysis:
        return False
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        return False
    service = observations.get("qwen_service")
    return isinstance(service, dict) and service.get("status") == "error"


def _image_selection_key(
    ref: str,
    analyses_by_image: dict[str, dict[str, Any]],
) -> tuple[float, int, int, str]:
    analysis = _analysis_for_ref(ref, analyses_by_image)
    timestamp = _analysis_timestamp(analysis)
    ocr = str(analysis.get("ocr_text") or "") if analysis else ""
    return (timestamp, 1 if ocr.strip() else 0, len(ocr), ref)


def _analysis_timestamp(analysis: dict[str, Any] | None) -> float:
    if not analysis:
        return 0.0
    value = analysis.get("timestamp")
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    frame_id = analysis.get("frame_id")
    if isinstance(frame_id, str):
        digits = "".join(ch for ch in frame_id if ch.isdigit())
        if digits:
            return float(int(digits))
    return 0.0


def _unique(values: Any) -> list[Any]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _render_scene(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
    image_prefix: str,
) -> list[str]:
    lines = ["### " + scene.title, ""]
    if scene.summary:
        lines.extend([scene.summary, ""])
    if scene.primary_image_ref:
        image_name = Path(scene.primary_image_ref).name
        analysis = _analysis_for_ref(scene.primary_image_ref, analyses_by_image)
        alt_text = _image_alt_text(scene.primary_image_ref, analysis)
        lines.append(f"![{alt_text}]({image_prefix}/{image_name})")
        if analysis:
            lines.extend(["", "**完成态画面**", ""])
            ocr = str(analysis.get("ocr_text") or "").strip()
            desc = str(analysis.get("vision_description") or "").strip()
            if ocr:
                lines.append(f"- OCR：{ocr}")
            if desc:
                lines.append(f"- 画面理解：{desc}")
            lines.append("")
    if scene.key_points:
        lines.extend(["**知识要点**", ""])
        lines.extend(f"- {point}" for point in scene.key_points)
        lines.append("")
    return lines


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
