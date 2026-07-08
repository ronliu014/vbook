"""vtext-first vault note enhancement export."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vbook_export.vault_preview import (
    PreviewScene,
    build_preview_scenes,
    load_preview_sources,
)


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


def write_vtext_first_package(
    vtext_note_path: Path | str,
    lesson_output_dir: Path | str,
    output_note_path: Path | str,
    manifest_path: Path | str | None = None,
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

    analyses_by_image = _analyses_by_image_path(sources.vision)
    scenes = [
        scene
        for scene in build_preview_scenes(sources)
        if scene.primary_image_ref is not None
    ]
    inserts = _build_visual_inserts(
        scenes=scenes,
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
    return str(path).replace("\\", "/")
