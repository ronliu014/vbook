from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_NOTE_PREFERENCE = ("note.md", "enhancement.md")


@dataclass(frozen=True)
class PublicationPlanPackage:
    output_dir: Path
    json_path: Path
    markdown_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a dry-run plan for publishing reviewed vBook notes to vault."
    )
    parser.add_argument("--experiment-root", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--target-vault-root", required=True)
    parser.add_argument("--plan-id", required=True)
    args = parser.parse_args(argv)

    package = create_publication_plan(
        experiment_root=args.experiment_root,
        route=args.route,
        variant=args.variant,
        target_vault_root=args.target_vault_root,
        plan_id=args.plan_id,
    )
    print(str(package.output_dir))
    return 0


def create_publication_plan(
    *,
    experiment_root: Path | str,
    route: str,
    variant: str,
    target_vault_root: Path | str,
    plan_id: str,
) -> PublicationPlanPackage:
    root = Path(experiment_root)
    output_dir = _plan_output_dir(root, plan_id)
    plan = _build_plan(
        experiment_root=root,
        route=route,
        variant=variant,
        target_vault_root=Path(target_vault_root),
        plan_id=plan_id,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "publication-plan.json"
    markdown_path = output_dir / "publication-plan.md"
    json_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(plan), encoding="utf-8")
    return PublicationPlanPackage(
        output_dir=output_dir,
        json_path=json_path,
        markdown_path=markdown_path,
    )


def _build_plan(
    *,
    experiment_root: Path,
    route: str,
    variant: str,
    target_vault_root: Path,
    plan_id: str,
) -> dict[str, Any]:
    items = []
    render_root = experiment_root / "renders" / route / variant
    if render_root.is_dir():
        for lesson_dir in sorted(path for path in render_root.iterdir() if path.is_dir()):
            item = _publication_item(
                lesson_dir=lesson_dir,
                target_vault_root=target_vault_root,
            )
            if item is not None:
                items.append(item)
    return {
        "schema_version": "1",
        "kind": "vault_publication_dry_run_plan",
        "plan_id": plan_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "safety": {
            "vault_write": "disabled",
            "source_renders": "read_only",
        },
        "experiment_root": str(experiment_root),
        "route": route,
        "variant": variant,
        "target_vault_root": str(target_vault_root),
        "item_count": len(items),
        "total_asset_count": sum(int(item["asset_count"]) for item in items),
        "total_markdown_image_count": sum(
            int(item["markdown_image_count"]) for item in items
        ),
        "total_missing_image_count": sum(
            int(item["missing_image_count"]) for item in items
        ),
        "items": items,
    }


def _publication_item(
    *,
    lesson_dir: Path,
    target_vault_root: Path,
) -> dict[str, Any] | None:
    note = _note_path_for_lesson(lesson_dir)
    if note is None:
        return None
    lesson = lesson_dir.name
    target_note = target_vault_root / f"{lesson}.md"
    target_assets_dir = target_vault_root / "assets" / lesson
    image_links = _markdown_image_links(note)
    resolved = [_resolve_markdown_link(note, link) for link in image_links]
    existing_images = [path for path in resolved if path.is_file()]
    missing_images = [path for path in resolved if not path.is_file()]
    assets = _unique_paths(existing_images)
    asset_targets = [
        {
            "source": str(asset),
            "target": str(target_assets_dir / asset.name),
        }
        for asset in assets
    ]
    return {
        "lesson": lesson,
        "source_note": str(note),
        "target_note": str(target_note),
        "source_assets_dir": str(lesson_dir / "assets"),
        "target_assets_dir": str(target_assets_dir),
        "asset_count": len(assets),
        "markdown_image_count": len(image_links),
        "resolved_image_count": len(existing_images),
        "missing_image_count": len(missing_images),
        "missing_images": [str(path) for path in missing_images],
        "assets": asset_targets,
    }


def _note_path_for_lesson(lesson_dir: Path) -> Path | None:
    for name in _NOTE_PREFERENCE:
        candidate = lesson_dir / name
        if candidate.is_file():
            return candidate
    markdown_files = sorted(lesson_dir.glob("*.md"))
    return markdown_files[0] if markdown_files else None


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    unique = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _markdown_image_links(note: Path) -> list[str]:
    markdown = note.read_text(encoding="utf-8")
    links = []
    for match in _IMAGE_LINK_RE.finditer(markdown):
        target = _strip_optional_title(match.group(1).strip())
        if _is_external_or_anchor_link(target):
            continue
        links.append(target)
    return links


def _strip_optional_title(target: str) -> str:
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    if " " not in target:
        return target
    return target.split(" ", 1)[0]


def _is_external_or_anchor_link(target: str) -> bool:
    if target.startswith("#"):
        return True
    parsed = urlparse(target)
    return bool(parsed.scheme and parsed.scheme.lower() not in {"", "file"})


def _resolve_markdown_link(note: Path, target: str) -> Path:
    decoded = unquote(target)
    parsed = urlparse(decoded)
    if parsed.scheme.lower() == "file":
        return Path(parsed.path)
    path = Path(decoded)
    if path.is_absolute():
        return path
    return note.parent / path


def _plan_output_dir(experiment_root: Path, plan_id: str) -> Path:
    root = experiment_root.resolve()
    plans_root = (root / "publication-plans").resolve()
    output_dir = (plans_root / plan_id).resolve()
    try:
        output_dir.relative_to(plans_root)
    except ValueError:
        raise ValueError(f"publication plan output escapes plans root: {plan_id}")
    return output_dir


def _render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Dry Run: {plan['plan_id']}",
        "",
        f"- Route: `{plan['route']}`",
        f"- Variant: `{plan['variant']}`",
        f"- Experiment: `{plan['experiment_root']}`",
        f"- Target vault root: `{plan['target_vault_root']}`",
        "- vault_write: disabled",
        f"- Notes: {plan['item_count']}",
        f"- Assets: {plan['total_asset_count']}",
        f"- Markdown images: {plan['total_markdown_image_count']}",
        f"- Missing images: {plan['total_missing_image_count']}",
        "",
        "## Items",
        "",
    ]
    if not plan["items"]:
        lines.append("No publishable note previews found.")
        return "\n".join(lines).rstrip() + "\n"
    for item in plan["items"]:
        lines.extend(
            [
                f"### {item['lesson']}",
                "",
                f"- Source note: `{item['source_note']}`",
                f"- Target note: `{item['target_note']}`",
                f"- Source assets: `{item['source_assets_dir']}`",
                f"- Target assets: `{item['target_assets_dir']}`",
                f"- Asset count: {item['asset_count']}",
                f"- Markdown images: {item['markdown_image_count']}",
                f"- Missing images: {item['missing_image_count']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
