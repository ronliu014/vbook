from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PublicationResult:
    status: str
    plan_path: Path
    result_json_path: Path
    result_markdown_path: Path
    copied_note_count: int
    copied_asset_count: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply an approved vBook vault publication plan."
    )
    parser.add_argument("--plan", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-plan-id")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    result = publish_from_plan(
        plan_path=args.plan,
        apply=args.apply,
        confirm_plan_id=args.confirm_plan_id,
        overwrite=args.overwrite,
    )
    print(str(result.result_json_path))
    return 0


def publish_from_plan(
    *,
    plan_path: Path | str,
    apply: bool,
    confirm_plan_id: str | None,
    overwrite: bool,
) -> PublicationResult:
    path = Path(plan_path)
    plan = _read_plan(path)
    _validate_plan(plan)
    plan_id = str(plan.get("plan_id") or "")
    if apply and confirm_plan_id != plan_id:
        raise ValueError("confirm_plan_id must match the publication plan id")

    result_dir = path.parent
    result_json_path = result_dir / "publication-result.json"
    result_markdown_path = result_dir / "publication-result.md"

    copied_notes: list[dict[str, str]] = []
    copied_assets: list[dict[str, str]] = []
    if apply:
        _validate_targets(plan=plan, overwrite=overwrite)
        copied_notes, copied_assets = _copy_plan_files(plan)

    status = "applied" if apply else "dry_run"
    result = PublicationResult(
        status=status,
        plan_path=path,
        result_json_path=result_json_path,
        result_markdown_path=result_markdown_path,
        copied_note_count=len(copied_notes),
        copied_asset_count=len(copied_assets),
    )
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_result",
        "plan_id": plan_id,
        "status": status,
        "applied": apply,
        "overwrite": overwrite,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_path": str(path),
        "copied_note_count": len(copied_notes),
        "copied_asset_count": len(copied_assets),
        "copied_notes": copied_notes,
        "copied_assets": copied_assets,
    }
    result_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result_markdown_path.write_text(_render_result_markdown(payload), encoding="utf-8")
    return result


def _read_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("publication plan must be a JSON object")
    return data


def _validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("kind") != "vault_publication_dry_run_plan":
        raise ValueError("unsupported publication plan kind")
    if plan.get("dry_run") is not True:
        raise ValueError("publication plan must be a dry-run plan")
    if int(plan.get("total_missing_image_count") or 0) != 0:
        raise ValueError("publication plan has missing images")
    if not plan.get("items"):
        raise ValueError("publication plan has no items")


def _validate_targets(*, plan: dict[str, Any], overwrite: bool) -> None:
    target_root = Path(str(plan.get("target_vault_root") or "")).resolve()
    for item in _plan_items(plan):
        target_note = Path(str(item.get("target_note") or "")).resolve()
        _require_under(target_note, target_root)
        _require_source_file(Path(str(item.get("source_note") or "")))
        if target_note.exists() and not overwrite:
            raise FileExistsError(f"target note already exists: {target_note}")
        for asset in item.get("assets", []):
            if not isinstance(asset, dict):
                continue
            source = Path(str(asset.get("source") or ""))
            target = Path(str(asset.get("target") or "")).resolve()
            _require_under(target, target_root)
            _require_source_file(source)
            if target.exists() and not overwrite:
                raise FileExistsError(f"target asset already exists: {target}")


def _copy_plan_files(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    copied_notes: list[dict[str, str]] = []
    copied_assets: list[dict[str, str]] = []
    for item in _plan_items(plan):
        source_note = Path(str(item["source_note"]))
        target_note = Path(str(item["target_note"]))
        target_note.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_note, target_note)
        copied_notes.append({"source": str(source_note), "target": str(target_note)})
        for asset in item.get("assets", []):
            if not isinstance(asset, dict):
                continue
            source = Path(str(asset["source"]))
            target = Path(str(asset["target"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied_assets.append({"source": str(source), "target": str(target)})
    return copied_notes, copied_assets


def _plan_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in plan.get("items", []) if isinstance(item, dict)]


def _require_source_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"source file does not exist: {path}")


def _require_under(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError(f"target path is outside target vault root: {path}")


def _render_result_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Result: {payload['plan_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Applied: `{payload['applied']}`",
        f"- Overwrite: `{payload['overwrite']}`",
        f"- Copied notes: {payload['copied_note_count']}",
        f"- Copied assets: {payload['copied_asset_count']}",
        "",
        "## Notes",
        "",
    ]
    if not payload["copied_notes"]:
        lines.append("No notes copied.")
    else:
        for item in payload["copied_notes"]:
            lines.append(f"- `{item['source']}` -> `{item['target']}`")
    lines.extend(["", "## Assets", ""])
    if not payload["copied_assets"]:
        lines.append("No assets copied.")
    else:
        for item in payload["copied_assets"]:
            lines.append(f"- `{item['source']}` -> `{item['target']}`")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
