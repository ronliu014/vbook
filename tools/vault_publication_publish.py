from __future__ import annotations

import argparse
import hashlib
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
    backup_dir: Path | None = None
    backed_up_note_count: int = 0
    backed_up_asset_count: int = 0


@dataclass(frozen=True)
class PublicationConflictReport:
    status: str
    plan_path: Path
    json_path: Path
    markdown_path: Path
    note_conflict_count: int
    asset_conflict_count: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply an approved vBook vault publication plan."
    )
    parser.add_argument("--plan", required=True)
    parser.add_argument(
        "--conflict-report",
        action="store_true",
        help="Write a read-only target conflict report and do not copy files.",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-plan-id")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--backup-existing",
        action="store_true",
        help="Back up existing target files before an overwrite apply.",
    )
    parser.add_argument("--backup-dir")
    args = parser.parse_args(argv)

    if args.conflict_report:
        report = create_publication_conflict_report(plan_path=args.plan)
        print(str(report.json_path))
        return 0

    result = publish_from_plan(
        plan_path=args.plan,
        apply=args.apply,
        confirm_plan_id=args.confirm_plan_id,
        overwrite=args.overwrite,
        backup_existing=args.backup_existing,
        backup_dir=args.backup_dir,
    )
    print(str(result.result_json_path))
    return 0


def publish_from_plan(
    *,
    plan_path: Path | str,
    apply: bool,
    confirm_plan_id: str | None,
    overwrite: bool,
    backup_existing: bool = False,
    backup_dir: Path | str | None = None,
) -> PublicationResult:
    path = Path(plan_path)
    plan = _read_plan(path)
    _validate_plan(plan)
    plan_id = str(plan.get("plan_id") or "")
    if apply and confirm_plan_id != plan_id:
        raise ValueError("confirm_plan_id must match the publication plan id")
    if backup_existing and not (apply and overwrite):
        raise ValueError("backup_existing requires apply and overwrite")

    result_dir = path.parent
    result_json_path = result_dir / "publication-result.json"
    result_markdown_path = result_dir / "publication-result.md"

    copied_notes: list[dict[str, str]] = []
    copied_assets: list[dict[str, str]] = []
    backed_up_notes: list[dict[str, Any]] = []
    backed_up_assets: list[dict[str, Any]] = []
    resolved_backup_dir: Path | None = None
    if apply:
        _validate_targets(plan=plan, overwrite=overwrite)
        if backup_existing:
            resolved_backup_dir = (
                Path(backup_dir) if backup_dir is not None else _default_backup_dir(path)
            )
            backed_up_notes, backed_up_assets = _backup_existing_targets(
                plan=plan,
                backup_dir=resolved_backup_dir,
            )
        copied_notes, copied_assets = _copy_plan_files(plan)

    status = "applied" if apply else "dry_run"
    result = PublicationResult(
        status=status,
        plan_path=path,
        result_json_path=result_json_path,
        result_markdown_path=result_markdown_path,
        copied_note_count=len(copied_notes),
        copied_asset_count=len(copied_assets),
        backup_dir=resolved_backup_dir,
        backed_up_note_count=len(backed_up_notes),
        backed_up_asset_count=len(backed_up_assets),
    )
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_result",
        "plan_id": plan_id,
        "status": status,
        "applied": apply,
        "overwrite": overwrite,
        "backup_existing": backup_existing,
        "backup_dir": str(resolved_backup_dir) if resolved_backup_dir else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_path": str(path),
        "copied_note_count": len(copied_notes),
        "copied_asset_count": len(copied_assets),
        "backed_up_note_count": len(backed_up_notes),
        "backed_up_asset_count": len(backed_up_assets),
        "backed_up_notes": backed_up_notes,
        "backed_up_assets": backed_up_assets,
        "copied_notes": copied_notes,
        "copied_assets": copied_assets,
    }
    result_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result_markdown_path.write_text(_render_result_markdown(payload), encoding="utf-8")
    return result


def create_publication_conflict_report(
    *, plan_path: Path | str
) -> PublicationConflictReport:
    path = Path(plan_path)
    plan = _read_plan(path)
    _validate_plan(plan)
    _validate_report_inputs(plan)

    json_path = path.parent / "publication-conflicts.json"
    markdown_path = path.parent / "publication-conflicts.md"
    items = [_conflict_item(plan_item) for plan_item in _plan_items(plan)]
    note_conflict_count = sum(
        1 for item in items if item["note"]["target_state"] == "exists"
    )
    asset_conflict_count = sum(
        1
        for item in items
        for asset in item["assets"]
        if asset["target_state"] == "exists"
    )
    status = (
        "conflicts_detected"
        if note_conflict_count or asset_conflict_count
        else "no_conflicts"
    )
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_conflict_report",
        "plan_id": str(plan.get("plan_id") or ""),
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "plan_path": str(path),
        "target_vault_root": str(plan.get("target_vault_root") or ""),
        "note_conflict_count": note_conflict_count,
        "asset_conflict_count": asset_conflict_count,
        "items": items,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_conflict_markdown(payload), encoding="utf-8")
    return PublicationConflictReport(
        status=status,
        plan_path=path,
        json_path=json_path,
        markdown_path=markdown_path,
        note_conflict_count=note_conflict_count,
        asset_conflict_count=asset_conflict_count,
    )


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


def _validate_report_inputs(plan: dict[str, Any]) -> None:
    target_root = Path(str(plan.get("target_vault_root") or "")).resolve()
    for item in _plan_items(plan):
        target_note = Path(str(item.get("target_note") or "")).resolve()
        _require_under(target_note, target_root)
        _require_source_file(Path(str(item.get("source_note") or "")))
        for asset in item.get("assets", []):
            if not isinstance(asset, dict):
                continue
            source = Path(str(asset.get("source") or ""))
            target = Path(str(asset.get("target") or "")).resolve()
            _require_under(target, target_root)
            _require_source_file(source)


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


def _backup_existing_targets(
    *, plan: dict[str, Any], backup_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_root = Path(str(plan.get("target_vault_root") or "")).resolve()
    files_dir = backup_dir / "files"
    backed_up_notes: list[dict[str, Any]] = []
    backed_up_assets: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for item in _plan_items(plan):
        target_note = Path(str(item.get("target_note") or "")).resolve()
        note_backup = _backup_target_file(
            target=target_note,
            target_root=target_root,
            files_dir=files_dir,
            seen_targets=seen_targets,
        )
        if note_backup is not None:
            backed_up_notes.append(note_backup)
        for asset in item.get("assets", []):
            if not isinstance(asset, dict):
                continue
            target = Path(str(asset.get("target") or "")).resolve()
            asset_backup = _backup_target_file(
                target=target,
                target_root=target_root,
                files_dir=files_dir,
                seen_targets=seen_targets,
            )
            if asset_backup is not None:
                backed_up_assets.append(asset_backup)
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_backup",
        "plan_id": str(plan.get("plan_id") or ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_vault_root": str(target_root),
        "backup_dir": str(backup_dir),
        "backed_up_note_count": len(backed_up_notes),
        "backed_up_asset_count": len(backed_up_assets),
        "backed_up_notes": backed_up_notes,
        "backed_up_assets": backed_up_assets,
    }
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "publication-backup.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (backup_dir / "publication-backup.md").write_text(
        _render_backup_markdown(payload),
        encoding="utf-8",
    )
    return backed_up_notes, backed_up_assets


def _backup_target_file(
    *,
    target: Path,
    target_root: Path,
    files_dir: Path,
    seen_targets: set[str],
) -> dict[str, Any] | None:
    if not target.is_file():
        return None
    key = str(target)
    if key in seen_targets:
        return None
    seen_targets.add(key)
    relative = target.relative_to(target_root)
    backup_path = files_dir / relative
    if backup_path.exists():
        raise FileExistsError(f"backup file already exists: {backup_path}")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup_path)
    return {
        "target": str(target),
        "backup": str(backup_path),
        "relative_path": str(relative),
        "size": target.stat().st_size,
        "sha256": _sha256(target),
    }


def _default_backup_dir(plan_path: Path) -> Path:
    return (
        plan_path.parent
        / "publication-backups"
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )


def _plan_items(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in plan.get("items", []) if isinstance(item, dict)]


def _conflict_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "lesson": str(item.get("lesson") or ""),
        "note": _file_conflict(
            source=Path(str(item.get("source_note") or "")),
            target=Path(str(item.get("target_note") or "")),
        ),
        "assets": [
            _file_conflict(
                source=Path(str(asset.get("source") or "")),
                target=Path(str(asset.get("target") or "")),
            )
            for asset in item.get("assets", [])
            if isinstance(asset, dict)
        ],
    }


def _file_conflict(*, source: Path, target: Path) -> dict[str, Any]:
    source_size = source.stat().st_size
    source_hash = _sha256(source)
    if target.is_file():
        target_size = target.stat().st_size
        target_hash = _sha256(target)
        hash_state = "same" if source_hash == target_hash else "different"
        without_overwrite = "skip_same" if hash_state == "same" else "block"
        with_overwrite = "skip_same" if hash_state == "same" else "overwrite"
    else:
        target_size = None
        target_hash = None
        hash_state = "missing"
        without_overwrite = "copy"
        with_overwrite = "copy"
    return {
        "source": str(source),
        "target": str(target),
        "target_state": "exists" if target.is_file() else "missing",
        "hash_state": hash_state,
        "source_size": source_size,
        "target_size": target_size,
        "source_sha256": source_hash,
        "target_sha256": target_hash,
        "planned_action_without_overwrite": without_overwrite,
        "planned_action_with_overwrite": with_overwrite,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        f"- Backup existing: `{payload['backup_existing']}`",
        f"- Backup dir: `{payload['backup_dir']}`",
        f"- Backed up notes: {payload['backed_up_note_count']}",
        f"- Backed up assets: {payload['backed_up_asset_count']}",
        f"- Copied notes: {payload['copied_note_count']}",
        f"- Copied assets: {payload['copied_asset_count']}",
        "",
        "## Backups",
        "",
    ]
    if not payload["backed_up_notes"] and not payload["backed_up_assets"]:
        lines.append("No existing targets backed up.")
    else:
        if payload["backed_up_notes"]:
            lines.append("Notes:")
            for item in payload["backed_up_notes"]:
                lines.append(f"- `{item['target']}` -> `{item['backup']}`")
        if payload["backed_up_assets"]:
            lines.append("")
            lines.append("Assets:")
            for item in payload["backed_up_assets"]:
                lines.append(f"- `{item['target']}` -> `{item['backup']}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
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


def _render_backup_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Backup: {payload['plan_id']}",
        "",
        f"- Target vault root: `{payload['target_vault_root']}`",
        f"- Backup dir: `{payload['backup_dir']}`",
        f"- Backed up notes: {payload['backed_up_note_count']}",
        f"- Backed up assets: {payload['backed_up_asset_count']}",
        "",
        "## Notes",
        "",
    ]
    if not payload["backed_up_notes"]:
        lines.append("No notes backed up.")
    else:
        for item in payload["backed_up_notes"]:
            lines.append(f"- `{item['target']}` -> `{item['backup']}`")
    lines.extend(["", "## Assets", ""])
    if not payload["backed_up_assets"]:
        lines.append("No assets backed up.")
    else:
        for item in payload["backed_up_assets"]:
            lines.append(f"- `{item['target']}` -> `{item['backup']}`")
    return "\n".join(lines).rstrip() + "\n"


def _render_conflict_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Conflicts: {payload['plan_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Target vault root: `{payload['target_vault_root']}`",
        f"- Existing target notes: {payload['note_conflict_count']}",
        f"- Existing target assets: {payload['asset_conflict_count']}",
        "",
        "## Items",
        "",
    ]
    for item in payload["items"]:
        lines.append(f"### {item['lesson']}")
        lines.append("")
        lines.extend(_render_conflict_file_lines("Note", item["note"]))
        if item["assets"]:
            lines.append("")
            lines.append("Assets:")
            for asset in item["assets"]:
                lines.extend(_render_conflict_file_lines("- Asset", asset))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_conflict_file_lines(label: str, file_item: dict[str, Any]) -> list[str]:
    return [
        f"{label}: `{file_item['target_state']}` / `{file_item['hash_state']}`",
        f"- source: `{file_item['source']}`",
        f"- target: `{file_item['target']}`",
        (
            "- planned without overwrite: "
            f"`{file_item['planned_action_without_overwrite']}`"
        ),
        (
            "- planned with overwrite: "
            f"`{file_item['planned_action_with_overwrite']}`"
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(main())
