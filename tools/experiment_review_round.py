from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_NOTE_FILE_PREFERENCE = ("note.md", "visual-evidence.md", "enhancement.md")
_REVIEW_COLUMNS = [
    "lesson",
    "route",
    "variant",
    "readable_note_candidate",
    "preview_path",
    "preflight_status",
    "semantic_coverage",
    "visual_recovery",
    "image_choice",
    "image_placement",
    "error_handling",
    "text_discipline",
    "traceability",
    "preview_safety",
    "user_preference",
    "reviewer_notes",
]


@dataclass(frozen=True)
class ReviewCandidate:
    lesson: str
    route: str
    variant: str
    preview_path: Path
    preflight_status: str

    @property
    def readable_note_candidate(self) -> str:
        return "yes" if self.route == "vtext_first_vault_enhance" else "no"

    def to_sheet_row(self) -> dict[str, str]:
        return {
            "lesson": self.lesson,
            "route": self.route,
            "variant": self.variant,
            "readable_note_candidate": self.readable_note_candidate,
            "preview_path": str(self.preview_path),
            "preflight_status": self.preflight_status,
            "semantic_coverage": "",
            "visual_recovery": "",
            "image_choice": "",
            "image_placement": "",
            "error_handling": "",
            "text_discipline": "",
            "traceability": "",
            "preview_safety": "",
            "user_preference": "",
            "reviewer_notes": "",
        }


@dataclass(frozen=True)
class ReviewRoundPackage:
    output_dir: Path
    manifest_path: Path
    review_sheet_path: Path
    user_review_path: Path
    decision_template_path: Path
    candidates: list[ReviewCandidate]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a standard vBook experiment user review round package."
    )
    parser.add_argument("--experiment-root", required=True)
    parser.add_argument("--round-id", required=True)
    parser.add_argument("--dataset-id", required=True)
    args = parser.parse_args(argv)

    package = create_review_round(
        experiment_root=args.experiment_root,
        round_id=args.round_id,
        dataset_id=args.dataset_id,
    )
    print(str(package.output_dir))
    return 0


def create_review_round(
    *,
    experiment_root: Path | str,
    round_id: str,
    dataset_id: str,
) -> ReviewRoundPackage:
    root = Path(experiment_root)
    output_dir = _review_output_dir(root, round_id)
    preflight_status_by_route = _load_preflight_status_by_route(root)
    candidates = _discover_candidates(root, preflight_status_by_route)

    output_dir.mkdir(parents=True, exist_ok=True)
    review_sheet_path = output_dir / "review-sheet.csv"
    manifest_path = output_dir / "review-manifest.json"
    user_review_path = output_dir / "user-review.md"
    decision_template_path = output_dir / "decision-template.md"

    _write_review_sheet(review_sheet_path, candidates)
    _write_manifest(
        manifest_path=manifest_path,
        experiment_root=root,
        output_dir=output_dir,
        round_id=round_id,
        dataset_id=dataset_id,
        candidates=candidates,
        preflight_status_by_route=preflight_status_by_route,
    )
    user_review_path.write_text(
        _render_user_review(
            round_id=round_id,
            dataset_id=dataset_id,
            experiment_root=root,
            candidates=candidates,
        ),
        encoding="utf-8",
    )
    decision_template_path.write_text(
        _render_decision_template(
            round_id=round_id,
            dataset_id=dataset_id,
            experiment_root=root,
            candidates=candidates,
        ),
        encoding="utf-8",
    )

    return ReviewRoundPackage(
        output_dir=output_dir,
        manifest_path=manifest_path,
        review_sheet_path=review_sheet_path,
        user_review_path=user_review_path,
        decision_template_path=decision_template_path,
        candidates=candidates,
    )


def _review_output_dir(experiment_root: Path, round_id: str) -> Path:
    root = experiment_root.resolve()
    reviews_root = (root / "reviews").resolve()
    output_dir = (reviews_root / round_id).resolve()
    if not _is_relative_to(output_dir, reviews_root):
        raise ValueError(f"review output escapes reviews root: {round_id}")
    return output_dir


def _discover_candidates(
    experiment_root: Path,
    preflight_status_by_route: dict[str, str],
) -> list[ReviewCandidate]:
    renders_dir = experiment_root / "renders"
    candidates: list[ReviewCandidate] = []
    if not renders_dir.is_dir():
        return candidates

    for route_dir in sorted(path for path in renders_dir.iterdir() if path.is_dir()):
        route = route_dir.name
        for variant_dir in sorted(path for path in route_dir.iterdir() if path.is_dir()):
            variant = variant_dir.name
            for lesson_dir in sorted(path for path in variant_dir.iterdir() if path.is_dir()):
                preview_path = _preview_path_for_lesson_dir(lesson_dir)
                if preview_path is None:
                    continue
                candidates.append(
                    ReviewCandidate(
                        lesson=lesson_dir.name,
                        route=route,
                        variant=variant,
                        preview_path=preview_path,
                        preflight_status=preflight_status_by_route.get(
                            route,
                            "not_applicable",
                        ),
                    )
                )
    return candidates


def _preview_path_for_lesson_dir(lesson_dir: Path) -> Path | None:
    for filename in _NOTE_FILE_PREFERENCE:
        candidate = lesson_dir / filename
        if candidate.is_file():
            return candidate
    markdown_files = sorted(lesson_dir.glob("*.md"))
    return markdown_files[0] if markdown_files else None


def _load_preflight_status_by_route(experiment_root: Path) -> dict[str, str]:
    comparisons_dir = experiment_root / "comparisons"
    statuses: dict[str, str] = {}
    if not comparisons_dir.is_dir():
        return statuses

    for path in sorted(comparisons_dir.glob("*preflight*.json")):
        data = _read_json_object(path)
        if data is None:
            continue
        route = _route_from_preflight_root(experiment_root, data.get("root"))
        if not route:
            continue
        statuses[route] = "pass" if data.get("ok") is True else "fail"
    return statuses


def _route_from_preflight_root(experiment_root: Path, value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        preflight_root = Path(value).resolve()
        renders_dir = (experiment_root / "renders").resolve()
        relative = preflight_root.relative_to(renders_dir)
    except (OSError, ValueError):
        return ""
    return relative.parts[0] if relative.parts else ""


def _write_review_sheet(path: Path, candidates: list[ReviewCandidate]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_REVIEW_COLUMNS)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(candidate.to_sheet_row())


def _write_manifest(
    *,
    manifest_path: Path,
    experiment_root: Path,
    output_dir: Path,
    round_id: str,
    dataset_id: str,
    candidates: list[ReviewCandidate],
    preflight_status_by_route: dict[str, str],
) -> None:
    manifest = {
        "schema_version": "1",
        "kind": "experiment_review_round",
        "round_id": round_id,
        "dataset_id": dataset_id,
        "experiment_root": str(experiment_root),
        "output_dir": str(output_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "preflight_status_by_route": preflight_status_by_route,
        "candidates": [
            {
                "lesson": candidate.lesson,
                "route": candidate.route,
                "variant": candidate.variant,
                "readable_note_candidate": candidate.readable_note_candidate,
                "preview_path": str(candidate.preview_path),
                "preflight_status": candidate.preflight_status,
            }
            for candidate in candidates
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _render_user_review(
    *,
    round_id: str,
    dataset_id: str,
    experiment_root: Path,
    candidates: list[ReviewCandidate],
) -> str:
    lines = [
        f"# User Review Round {round_id}",
        "",
        f"- Experiment: `{experiment_root}`",
        f"- Dataset: `{dataset_id}`",
        "- Scores use `0-3`; leave blank when not reviewed.",
        "",
        "## Review Rubric",
        "",
        "- Semantic coverage: does the note preserve important lesson meaning?",
        "- Visual recovery: does the route recover board/slide/chart information?",
        "- Image choice: is the selected image a high-value completed teaching page?",
        "- Image placement: is the image close to the matching section?",
        "- Error handling: are Qwen errors and placeholders absent?",
        "- Text discipline: does the note stay concise and grounded?",
        "- Traceability: can claims be linked to timestamps/images/source artifacts?",
        "- Preview safety: are paths and assets stable before vault publication?",
        "",
    ]
    by_lesson: dict[str, list[ReviewCandidate]] = {}
    for candidate in candidates:
        by_lesson.setdefault(candidate.lesson, []).append(candidate)

    for lesson in sorted(by_lesson):
        lines.extend([f"## {lesson}", ""])
        for candidate in sorted(
            by_lesson[lesson],
            key=lambda item: (item.route, item.variant),
        ):
            lines.extend(
                [
                    f"### {candidate.route} / {candidate.variant}",
                    "",
                    f"- Preview: `{candidate.preview_path}`",
                    f"- Readable note candidate: `{candidate.readable_note_candidate}`",
                    f"- Preflight: `{candidate.preflight_status}`",
                    "",
                    "Scores:",
                    "",
                    "- Semantic coverage:",
                    "- Visual recovery:",
                    "- Image choice:",
                    "- Image placement:",
                    "- Error handling:",
                    "- Text discipline:",
                    "- Traceability:",
                    "- Preview safety:",
                    "- User preference:",
                    "- Notes:",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _render_decision_template(
    *,
    round_id: str,
    dataset_id: str,
    experiment_root: Path,
    candidates: list[ReviewCandidate],
) -> str:
    routes = sorted({candidate.route for candidate in candidates})
    lines = [
        f"# Decision Template {round_id}",
        "",
        f"- Experiment: `{experiment_root}`",
        f"- Dataset: `{dataset_id}`",
        f"- Candidate routes: {', '.join(f'`{route}`' for route in routes)}",
        "",
        "## Decision",
        "",
        "- Best readable-note route:",
        "- Decision status: continue / revise / compare / abandon / candidate_for_production",
        "- Reason:",
        "",
        "## Evidence",
        "",
        "- Automatic preflight:",
        "- User preference:",
        "- Strongest lesson examples:",
        "- Must-fix issues:",
        "",
        "## Next Step",
        "",
        "-",
        "",
    ]
    return "\n".join(lines)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
