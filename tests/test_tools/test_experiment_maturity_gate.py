import json
import tempfile
import unittest
from pathlib import Path

from tools.experiment_maturity_gate import evaluate_maturity_gate


class ExperimentMaturityGateTest(unittest.TestCase):
    def test_passes_selected_route_with_three_lessons_and_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            _write_route_renders(root, "vtext_first_vault_enhance", ["L1", "L2", "L3"])
            _write_review_round(
                root,
                selected_route="vtext_first_vault_enhance",
                review_status="winner_selected",
                preflight_status="pass",
                user_preference="3",
            )

            report = evaluate_maturity_gate(
                experiment_root=root,
                route="vtext_first_vault_enhance",
                round_id="round-002",
            )

        self.assertEqual(report.status, "pass")
        self.assertTrue(report.ok)
        self.assertEqual(report.lesson_count, 3)
        self.assertEqual(report.selected_route, "vtext_first_vault_enhance")
        self.assertFalse(report.issues)

    def test_blocks_when_review_round_is_not_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            _write_route_renders(root, "vtext_first_vault_enhance", ["L1", "L2", "L3"])
            _write_review_round(
                root,
                selected_route="",
                review_status="pending",
                preflight_status="pass",
                user_preference="3",
            )

            report = evaluate_maturity_gate(
                experiment_root=root,
                route="vtext_first_vault_enhance",
                round_id="round-002",
            )

        self.assertEqual(report.status, "blocked")
        self.assertIn("review_not_finalized", {issue.code for issue in report.issues})

    def test_rejects_report_path_outside_comparisons_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            root.mkdir()

            with self.assertRaises(ValueError):
                evaluate_maturity_gate(
                    experiment_root=root,
                    route="vtext_first_vault_enhance",
                    round_id="round-002",
                    json_output=root / "reviews" / "gate.json",
                )


def _write_route_renders(root: Path, route: str, lessons: list[str]) -> None:
    for lesson in lessons:
        note = root / "renders" / route / "baseline" / lesson / "note.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"# {lesson}\n", encoding="utf-8")


def _write_review_round(
    root: Path,
    *,
    selected_route: str,
    review_status: str,
    preflight_status: str,
    user_preference: str,
) -> None:
    round_dir = root / "reviews" / "round-002"
    round_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1",
        "kind": "experiment_review_round",
        "round_id": "round-002",
        "dataset_id": "dataset",
        "candidate_count": 3,
        "preflight_status_by_route": {
            "vtext_first_vault_enhance": preflight_status,
        },
        "candidates": [
            {
                "lesson": lesson,
                "route": "vtext_first_vault_enhance",
                "variant": "baseline",
                "readable_note_candidate": "yes",
                "preview_path": str(
                    root
                    / "renders"
                    / "vtext_first_vault_enhance"
                    / "baseline"
                    / lesson
                    / "note.md"
                ),
                "preflight_status": preflight_status,
            }
            for lesson in ["L1", "L2", "L3"]
        ],
        "review_status": review_status,
        "selected_route": selected_route,
        "decision_status": "continue",
    }
    (round_dir / "review-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )
    rows = [
        "lesson,route,variant,readable_note_candidate,preview_path,preflight_status,"
        "semantic_coverage,visual_recovery,image_choice,image_placement,"
        "error_handling,text_discipline,traceability,preview_safety,"
        "user_preference,reviewer_notes",
    ]
    for lesson in ["L1", "L2", "L3"]:
        rows.append(
            f"{lesson},vtext_first_vault_enhance,baseline,yes,"
            f"{root / 'renders' / 'vtext_first_vault_enhance' / 'baseline' / lesson / 'note.md'},"
            f"{preflight_status},3,3,3,3,3,3,2,3,{user_preference},winner"
        )
    (round_dir / "review-sheet.csv").write_text(
        "\n".join(rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
