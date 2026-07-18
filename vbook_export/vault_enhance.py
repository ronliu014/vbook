"""vtext-first vault note enhancement export."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from vbook_export.vault_preview import (
    PreviewScene,
    build_preview_scenes,
    load_preview_sources,
)
from vbook_export.visual_selection import visual_value_key


_GENERIC_ENTITY_KEYWORDS = {
    "k线图",
    "交易软件",
    "股票交易",
    "股票分析",
    "黄金分割",
    "黄金分割线",
    "涨停板",
    "支撑位",
    "止损位",
    "画线工具",
}


@dataclass(frozen=True)
class VaultEnhancePackage:
    output_note_path: Path
    manifest_path: Path
    asset_paths: list[Path]


@dataclass(frozen=True)
class _MarkdownSection:
    heading_index: int
    end_index: int
    heading_level: int
    heading_text: str
    text: str


@dataclass(frozen=True)
class _VisualInsert:
    scene: PreviewScene
    image_path: Path
    relative_link: str
    caption: str


@dataclass(frozen=True)
class _ImageSelectionPolicy:
    max_images_per_note: int | None
    min_image_gap_seconds: float
    include_error_images: bool = False


@dataclass(frozen=True)
class _ImageSelectionResult:
    scenes: list[PreviewScene]
    skipped_error_image_count: int


def write_vtext_first_package(
    vtext_note_path: Path | str,
    lesson_output_dir: Path | str,
    output_note_path: Path | str,
    manifest_path: Path | str | None = None,
    max_images_per_note: int | None = None,
    min_image_gap_seconds: float = 0.0,
) -> VaultEnhancePackage:
    """Write a vBook-enhanced note while keeping the vtext source read-only."""
    sources = load_preview_sources(vtext_note_path, lesson_output_dir)
    output_path = Path(output_note_path)
    manifest = (
        Path(manifest_path)
        if manifest_path is not None
        else output_path.with_suffix(".manifest.json")
    )
    assets_dir = output_path.parent / "assets" / output_path.stem
    image_policy = _validate_image_selection_policy(
        max_images_per_note=max_images_per_note,
        min_image_gap_seconds=min_image_gap_seconds,
    )

    analyses_by_image = _analyses_by_image_path(sources.vision)
    scenes = [
        scene
        for scene in build_preview_scenes(sources)
        if scene.primary_image_ref is not None
    ]
    selection = _select_scenes_for_insertion(
        scenes=scenes,
        analyses_by_image=analyses_by_image,
        policy=image_policy,
    )
    inserts = _build_visual_inserts(
        scenes=selection.scenes,
        analyses_by_image=analyses_by_image,
        assets_dir=assets_dir,
        link_prefix=Path("assets") / output_path.stem,
    )
    markdown, inserted_count, unmatched_count = _insert_visuals(
        sources.vault_note_markdown,
        inserts,
        analyses_by_image,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    copied_assets = _copy_assets(inserts)
    output_path.write_text(markdown, encoding="utf-8")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "status": "preview",
                "text_source": "vtext",
                "source_note": str(Path(vtext_note_path)),
                "lesson_output_dir": str(Path(lesson_output_dir)),
                "output_note": str(output_path),
                "assets_dir": str(assets_dir),
                "inserted_image_count": inserted_count,
                "unmatched_image_count": unmatched_count,
                "image_selection": {
                    "max_images_per_note": image_policy.max_images_per_note,
                    "min_image_gap_seconds": image_policy.min_image_gap_seconds,
                    "candidate_scene_count": len(scenes),
                    "selected_scene_count": len(selection.scenes),
                    "skipped_error_image_count": selection.skipped_error_image_count,
                },
                "asset_count": len(copied_assets),
                "assets": [str(path) for path in copied_assets],
                "safety": {"source_vtext": "read_only"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return VaultEnhancePackage(
        output_note_path=output_path,
        manifest_path=manifest,
        asset_paths=copied_assets,
    )


def _validate_image_selection_policy(
    *,
    max_images_per_note: int | None,
    min_image_gap_seconds: float,
) -> _ImageSelectionPolicy:
    if max_images_per_note is not None and max_images_per_note < 0:
        raise ValueError("max_images_per_note must be greater than or equal to 0")
    if min_image_gap_seconds < 0:
        raise ValueError("min_image_gap_seconds must be greater than or equal to 0")
    return _ImageSelectionPolicy(
        max_images_per_note=max_images_per_note,
        min_image_gap_seconds=float(min_image_gap_seconds),
    )


def _select_scenes_for_insertion(
    *,
    scenes: list[PreviewScene],
    analyses_by_image: dict[str, dict[str, Any]],
    policy: _ImageSelectionPolicy,
) -> _ImageSelectionResult:
    skipped_error_count = 0
    eligible: list[PreviewScene] = []
    for scene in scenes:
        if scene.primary_image_ref is None:
            continue
        if (
            not policy.include_error_images
            and _analysis_has_qwen_error(
                _analysis_for_ref(scene.primary_image_ref, analyses_by_image)
            )
        ):
            skipped_error_count += 1
            continue
        eligible.append(scene)

    gap_filtered = _apply_min_gap_policy(
        eligible,
        analyses_by_image,
        policy.min_image_gap_seconds,
    )
    budgeted = _apply_max_images_policy(
        gap_filtered,
        analyses_by_image,
        policy.max_images_per_note,
    )
    return _ImageSelectionResult(
        scenes=budgeted,
        skipped_error_image_count=skipped_error_count,
    )


def _apply_min_gap_policy(
    scenes: list[PreviewScene],
    analyses_by_image: dict[str, dict[str, Any]],
    min_gap_seconds: float,
) -> list[PreviewScene]:
    if min_gap_seconds <= 0 or len(scenes) <= 1:
        return scenes
    ordered = sorted(scenes, key=_scene_timestamp)
    clusters: list[list[PreviewScene]] = []
    for scene in ordered:
        if not clusters:
            clusters.append([scene])
            continue
        previous_timestamp = _scene_timestamp(clusters[-1][-1])
        if _scene_timestamp(scene) - previous_timestamp < min_gap_seconds:
            clusters[-1].append(scene)
        else:
            clusters.append([scene])
    selected = [
        max(cluster, key=lambda scene: _scene_final_value_key(scene, analyses_by_image))
        for cluster in clusters
    ]
    return sorted(selected, key=lambda scene: scenes.index(scene))


def _apply_max_images_policy(
    scenes: list[PreviewScene],
    analyses_by_image: dict[str, dict[str, Any]],
    max_images_per_note: int | None,
) -> list[PreviewScene]:
    if max_images_per_note is None or len(scenes) <= max_images_per_note:
        return scenes
    ranked = sorted(
        scenes,
        key=lambda scene: _scene_budget_key(scene, analyses_by_image),
        reverse=True,
    )
    kept_ids = {id(scene) for scene in ranked[:max_images_per_note]}
    return [scene for scene in scenes if id(scene) in kept_ids]


def _scene_final_value_key(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
) -> tuple[int, float, int, int, int, float, str]:
    analysis = _analysis_for_scene(scene, analyses_by_image)
    return visual_value_key(analysis, _scene_timestamp(scene), scene.title)


def _scene_budget_key(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
) -> tuple[int, float, int, int, int, float, str]:
    analysis = _analysis_for_scene(scene, analyses_by_image)
    return visual_value_key(analysis, _scene_timestamp(scene), scene.title)


def _scene_timestamp(scene: PreviewScene) -> float:
    if scene.end_timestamp is not None:
        return scene.end_timestamp
    if scene.start_timestamp is not None:
        return scene.start_timestamp
    return 0.0


def _analysis_for_scene(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if scene.primary_image_ref is None:
        return None
    return _analysis_for_ref(scene.primary_image_ref, analyses_by_image)


def _analysis_confidence(analysis: dict[str, Any] | None) -> float:
    if not analysis:
        return 0.0
    confidence = analysis.get("confidence")
    if isinstance(confidence, bool):
        return 0.0
    if isinstance(confidence, (int, float)):
        return float(confidence)
    return 0.0


def _build_visual_inserts(
    *,
    scenes: list[PreviewScene],
    analyses_by_image: dict[str, dict[str, Any]],
    assets_dir: Path,
    link_prefix: Path,
) -> list[_VisualInsert]:
    inserts = []
    for scene in scenes:
        if scene.primary_image_ref is None:
            continue
        source_image = Path(scene.primary_image_ref)
        if not source_image.is_file():
            raise ValueError(f"selected image does not exist: {source_image}")
        analysis = _analysis_for_ref(scene.primary_image_ref, analyses_by_image)
        inserts.append(
            _VisualInsert(
                scene=scene,
                image_path=assets_dir / source_image.name,
                relative_link=_markdown_path(link_prefix / source_image.name),
                caption=_caption_for_scene(scene, analysis),
            )
        )
    return inserts


def _insert_visuals(
    markdown: str,
    inserts: list[_VisualInsert],
    analyses_by_image: dict[str, dict[str, Any]],
) -> tuple[str, int, int]:
    lines = markdown.rstrip("\n").splitlines()
    sections = _markdown_sections(lines)
    by_section: dict[int, list[_VisualInsert]] = {}
    unmatched: list[_VisualInsert] = []
    for insert in inserts:
        section_index = _best_section_index(insert.scene, sections, analyses_by_image)
        if section_index is None:
            unmatched.append(insert)
        else:
            by_section.setdefault(section_index, []).append(insert)

    for section_index in sorted(by_section.keys(), reverse=True):
        section = sections[section_index]
        insert_at = _section_insert_index(lines, section.heading_index)
        block = _render_insert_block(by_section[section_index])
        lines[insert_at:insert_at] = block

    if unmatched:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(["## 图示补充待确认", ""])
        lines.extend(_render_insert_block(unmatched))

    return "\n".join(lines).rstrip() + "\n", len(inserts) - len(unmatched), len(unmatched)


def _markdown_sections(lines: list[str]) -> list[_MarkdownSection]:
    heading_indexes = [
        index for index, line in enumerate(lines) if _heading_parts(line) is not None
    ]
    sections = []
    for offset, heading_index in enumerate(heading_indexes):
        end_index = (
            heading_indexes[offset + 1]
            if offset + 1 < len(heading_indexes)
            else len(lines)
        )
        heading_level, heading_text = _heading_parts(lines[heading_index]) or (1, "")
        sections.append(
            _MarkdownSection(
                heading_index=heading_index,
                end_index=end_index,
                heading_level=heading_level,
                heading_text=heading_text,
                text=_section_matching_text(lines[heading_index:end_index]),
            )
        )
    return sections


def _section_matching_text(lines: list[str]) -> str:
    match_lines = []
    for line in lines:
        if _is_source_quote_start(line):
            break
        match_lines.append(line)
    return "\n".join(match_lines)


def _is_source_quote_start(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("> [!quote") and "原文" in stripped


def _best_section_index(
    scene: PreviewScene,
    sections: list[_MarkdownSection],
    analyses_by_image: dict[str, dict[str, Any]],
) -> int | None:
    scored = [
        (index, _match_score(scene, section, analyses_by_image), section.heading_level)
        for index, section in enumerate(sections)
    ]
    specific_scored = [item for item in scored if item[2] > 1 and item[1] > 0]
    candidates = specific_scored or scored
    best_index = None
    best_score = 0
    best_heading_level = 0
    for index, score, heading_level in candidates:
        if score > best_score or (
            score == best_score and heading_level > best_heading_level
        ):
            best_score = score
            best_index = index
            best_heading_level = heading_level
    return best_index if best_score >= 2 else None


def _match_score(
    scene: PreviewScene,
    section: _MarkdownSection,
    analyses_by_image: dict[str, dict[str, Any]],
) -> int:
    section_text = _normalize_text(section.text)
    heading_text = _normalize_text(_clean_heading_for_match(section.heading_text))
    score = 0
    for term in _scene_terms(scene, analyses_by_image):
        normalized = _normalize_text(term)
        if len(normalized) < 2:
            continue
        if normalized in heading_text:
            score += 3
        elif normalized in section_text:
            score += 1
        elif heading_text and heading_text in normalized:
            score += 2
        score += _keyword_overlap_score(term, section_text, heading_text)
        score += _entity_overlap_score(term, section_text, heading_text)
    return score


def _scene_terms(
    scene: PreviewScene,
    analyses_by_image: dict[str, dict[str, Any]],
) -> list[str]:
    terms = [scene.title]
    if scene.primary_image_ref:
        analysis = _analysis_for_ref(scene.primary_image_ref, analyses_by_image)
        if analysis:
            terms.extend(
                [
                    str(analysis.get("ocr_text") or ""),
                    str(analysis.get("vision_description") or ""),
                    _analysis_topic(analysis),
                ]
            )
    expanded = []
    for term in terms:
        expanded.append(term)
        expanded.extend(_domain_aliases(term))
    return expanded


def _section_insert_index(lines: list[str], heading_index: int) -> int:
    insert_at = heading_index + 1
    while insert_at < len(lines) and lines[insert_at] == "":
        insert_at += 1
    return insert_at


def _render_insert_block(inserts: list[_VisualInsert]) -> list[str]:
    block: list[str] = []
    for insert in inserts:
        if block and block[-1] != "":
            block.append("")
        block.extend(
            [
                f"![{insert.scene.title}]({insert.relative_link})",
                "",
                f"> 图示补充：{insert.caption}",
                "",
            ]
        )
    return block


def _copy_assets(inserts: list[_VisualInsert]) -> list[Path]:
    copied: list[Path] = []
    seen: set[Path] = set()
    for insert in inserts:
        if insert.image_path in seen:
            continue
        insert.image_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(insert.scene.primary_image_ref or ""), insert.image_path)
        copied.append(insert.image_path)
        seen.add(insert.image_path)
    return copied


def _caption_for_scene(
    scene: PreviewScene,
    analysis: dict[str, Any] | None,
) -> str:
    if analysis:
        description = str(analysis.get("vision_description") or "").strip()
        if description:
            return description
        ocr = str(analysis.get("ocr_text") or "").strip()
        if ocr:
            return "画面呈现：" + "；".join(line.strip() for line in ocr.splitlines() if line.strip())
    if scene.summary:
        return scene.summary
    return scene.title


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


def _analysis_topic(analysis: dict[str, Any]) -> str:
    observations = analysis.get("structured_observations")
    if not isinstance(observations, dict):
        return ""
    topic = observations.get("topic")
    return topic if isinstance(topic, str) else ""


def _heading_parts(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _clean_heading_for_match(value: str) -> str:
    return re.sub(r"^([0-9]+[.)、.]|[一二三四五六七八九十]+、)\s*", "", value).strip()


def _keyword_overlap_score(term: str, section_text: str, heading_text: str) -> int:
    score = 0
    for keyword in _matching_keywords(term):
        normalized = _normalize_text(keyword)
        if len(normalized) < 2:
            continue
        if normalized in heading_text:
            score += 2
        elif normalized in section_text:
            score += 1
    return min(score, 6)


def _entity_overlap_score(term: str, section_text: str, heading_text: str) -> int:
    score = 0
    for keyword in _entity_keywords(term):
        normalized = _normalize_text(keyword)
        if len(normalized) < 3:
            continue
        if normalized in heading_text:
            score += 8
    return min(score, 12)


def _matching_keywords(value: str) -> list[str]:
    keywords: list[str] = []
    for word in re.findall(r"[A-Za-z0-9_]{3,}", value.lower()):
        keywords.append(word)
    for cjk_run in re.findall(r"[\u4e00-\u9fff]{2,}", value):
        if len(cjk_run) <= 4:
            keywords.append(cjk_run)
            continue
        keywords.extend(cjk_run[index : index + 2] for index in range(len(cjk_run) - 1))
    return _unique(keywords)


def _entity_keywords(value: str) -> list[str]:
    keywords: list[str] = []
    keywords.extend(re.findall(r"(?<!\d)\d{6}(?!\d)", value))
    for cjk_run in re.findall(r"[\u4e00-\u9fff]{3,}", value):
        max_size = min(6, len(cjk_run))
        for size in range(3, max_size + 1):
            for index in range(len(cjk_run) - size + 1):
                _append_entity_keyword(keywords, cjk_run[index : index + size])
    return _unique(keywords)


def _append_entity_keyword(keywords: list[str], keyword: str) -> None:
    normalized = _normalize_text(keyword)
    if normalized in _GENERIC_ENTITY_KEYWORDS:
        return
    keywords.append(keyword)


def _domain_aliases(value: str) -> list[str]:
    aliases = []
    if "养殖" in value:
        aliases.append(value.replace("养殖", "养股"))
    if "养殖方法" in value:
        aliases.append(value.replace("养殖方法", "养股策略"))
    if "养股" in value:
        aliases.append(value.replace("养股", "养殖"))
    return aliases


def _unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _markdown_path(path: Path) -> str:
    return "/".join(quote(part, safe="") for part in path.parts)
