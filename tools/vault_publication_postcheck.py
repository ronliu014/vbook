from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote


_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class PublicationPostcheckPackage:
    status: str
    json_path: Path
    markdown_path: Path


def run_publication_postcheck(
    *, publication_result_path: Path | str
) -> PublicationPostcheckPackage:
    path = Path(publication_result_path)
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if result.get("kind") != "vault_publication_result":
        raise ValueError("unsupported publication result kind")
    if result.get("status") != "applied":
        raise ValueError("publication result must be applied")
    file_checks = []
    for pair in list(result.get("copied_notes", [])) + list(
        result.get("copied_assets", [])
    ):
        if not isinstance(pair, dict):
            continue
        source = Path(str(pair.get("source") or ""))
        target = Path(str(pair.get("target") or ""))
        source_hash = _sha256(source) if source.is_file() else None
        target_hash = _sha256(target) if target.is_file() else None
        file_checks.append(
            {
                "source": str(source),
                "target": str(target),
                "source_exists": source.is_file(),
                "target_exists": target.is_file(),
                "source_sha256": source_hash,
                "target_sha256": target_hash,
                "hash_match": source_hash is not None and source_hash == target_hash,
            }
        )
    image_checks = []
    for pair in result.get("copied_notes", []):
        if not isinstance(pair, dict):
            continue
        note = Path(str(pair.get("target") or ""))
        if not note.is_file():
            continue
        for raw_link in _markdown_image_links(note):
            resolved = (note.parent / unquote(raw_link)).resolve()
            image_checks.append(
                {
                    "note": str(note),
                    "link": raw_link,
                    "resolved": str(resolved),
                    "exists": resolved.is_file(),
                }
            )
    mismatch_count = sum(1 for item in file_checks if not item["hash_match"])
    missing_image_count = sum(1 for item in image_checks if not item["exists"])
    status = "pass" if mismatch_count == 0 and missing_image_count == 0 else "fail"
    payload = {
        "schema_version": "1",
        "kind": "vault_publication_postcheck",
        "plan_id": str(result.get("plan_id") or ""),
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "publication_result": str(path),
        "file_check_count": len(file_checks),
        "hash_match_count": sum(1 for item in file_checks if item["hash_match"]),
        "hash_mismatch_count": mismatch_count,
        "markdown_image_link_count": len(image_checks),
        "missing_markdown_image_count": missing_image_count,
        "file_checks": file_checks,
        "markdown_image_checks": image_checks,
    }
    json_path = path.parent / "publication-postcheck.json"
    markdown_path = path.parent / "publication-postcheck.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_postcheck_markdown(payload), encoding="utf-8")
    return PublicationPostcheckPackage(
        status=status,
        json_path=json_path,
        markdown_path=markdown_path,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _markdown_image_links(note: Path) -> list[str]:
    links = []
    markdown = note.read_text(encoding="utf-8")
    for match in _IMAGE_LINK_RE.finditer(markdown):
        target = match.group(1).strip()
        if ' "' in target:
            target = target.split(' "', 1)[0].strip()
        if target.startswith(("http://", "https://", "#")):
            continue
        links.append(target)
    return links


def _render_postcheck_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Vault Publication Postcheck: {payload['plan_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- File checks: {payload['file_check_count']}",
        f"- Hash matches: {payload['hash_match_count']}",
        f"- Hash mismatches: {payload['hash_mismatch_count']}",
        f"- Markdown image links: {payload['markdown_image_link_count']}",
        f"- Missing Markdown images: {payload['missing_markdown_image_count']}",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an applied vault publication result.")
    parser.add_argument("--publication-result", required=True)
    args = parser.parse_args(argv)
    package = run_publication_postcheck(publication_result_path=args.publication_result)
    print(str(package.json_path))
    return 0 if package.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
