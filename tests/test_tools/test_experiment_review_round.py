import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.experiment_review_round import create_review_round


class ExperimentReviewRoundTest(unittest.TestCase):
    def test_generates_review_round_files_from_rendered_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "E20260711-existing-model-baselines"
            _write_note(
                root
                / "renders"
                / "vtext_first_vault_enhance"
                / "baseline"
                / "如何筛选龙头股？"
                / "note.md",
                "# 如何筛选龙头股？\n",
            )
            _write_note(
                root
                / "renders"
                / "qwen_visual_evidence_240s"
                / "baseline"
                / "如何筛选龙头股？"
                / "visual-evidence.md",
                "# Qwen Evidence\n",
            )
            _write_preflight(
                root / "comparisons" / "vtext-first-preflight.json",
                root / "renders" / "vtext_first_vault_enhance" / "baseline",
                ok=True,
            )

            package = create_review_round(
                experiment_root=root,
                round_id="round-002",
                dataset_id="investment-camp-hanke-basic-v1",
            )

            self.assertTrue(package.manifest_path.is_file())
            self.assertTrue(package.review_sheet_path.is_file())
            self.assertTrue(package.user_review_path.is_file())
            self.assertTrue(package.decision_template_path.is_file())

            rows = _read_csv(package.review_sheet_path)
            self.assertEqual(len(rows), 2)
            by_route = {row["route"]: row for row in rows}
            self.assertEqual(
                by_route["vtext_first_vault_enhance"]["preflight_status"],
                "pass",
            )
            self.assertEqual(
                by_route["vtext_first_vault_enhance"]["readable_note_candidate"],
                "yes",
            )
            self.assertEqual(
                by_route["qwen_visual_evidence_240s"]["preflight_status"],
                "not_applicable",
            )
            self.assertEqual(
                by_route["qwen_visual_evidence_240s"]["readable_note_candidate"],
                "no",
            )
            self.assertTrue(by_route["vtext_first_vault_enhance"]["preview_path"])

            manifest = json.loads(
                package.manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["round_id"], "round-002")
            self.assertEqual(manifest["dataset_id"], "investment-camp-hanke-basic-v1")
            self.assertEqual(manifest["candidate_count"], 2)
            self.assertEqual(manifest["preflight_status_by_route"]["vtext_first_vault_enhance"], "pass")

            user_review = package.user_review_path.read_text(encoding="utf-8")
            self.assertIn("# User Review Round round-002", user_review)
            self.assertIn("## 如何筛选龙头股？", user_review)
            self.assertIn("vtext_first_vault_enhance", user_review)
            self.assertIn("qwen_visual_evidence_240s", user_review)

    def test_marks_failed_preflight_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            _write_note(
                root
                / "renders"
                / "vtext_first_vault_enhance"
                / "baseline"
                / "反抽 反弹 反转"
                / "note.md",
                "# 反抽 反弹 反转\n",
            )
            _write_preflight(
                root / "comparisons" / "vtext-first-preflight.json",
                root / "renders" / "vtext_first_vault_enhance" / "baseline",
                ok=False,
            )

            package = create_review_round(
                experiment_root=root,
                round_id="round-001",
                dataset_id="dataset",
            )

            rows = _read_csv(package.review_sheet_path)

        self.assertEqual(rows[0]["preflight_status"], "fail")

    def test_rejects_round_id_that_escapes_experiment_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            root.mkdir()

            with self.assertRaises(ValueError):
                create_review_round(
                    experiment_root=root,
                    round_id="../outside",
                    dataset_id="dataset",
                )


def _write_note(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def _write_preflight(path: Path, root: Path, *, ok: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "root": str(root),
                "ok": ok,
                "note_count": 1,
                "manifest_count": 1,
                "image_link_count": 1,
                "missing_image_count": 0 if ok else 1,
                "error_count": 0 if ok else 1,
                "warning_count": 0,
                "issues": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
