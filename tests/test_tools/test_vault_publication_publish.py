import json
import tempfile
import unittest
from pathlib import Path

from tools.vault_publication_publish import (
    create_publication_conflict_report,
    publish_from_plan,
)


class VaultPublicationPublishTest(unittest.TestCase):
    def test_dry_run_does_not_copy_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, target_note, target_asset = _write_plan(root)

            result = publish_from_plan(
                plan_path=plan_path,
                apply=False,
                confirm_plan_id=None,
                overwrite=False,
            )

            self.assertEqual(result.status, "dry_run")
            self.assertFalse(target_note.exists())
            self.assertFalse(target_asset.exists())

    def test_apply_with_matching_confirmation_copies_note_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, target_note, target_asset = _write_plan(root)

            result = publish_from_plan(
                plan_path=plan_path,
                apply=True,
                confirm_plan_id="plan-001",
                overwrite=False,
            )

            self.assertEqual(result.status, "applied")
            self.assertTrue(target_note.is_file())
            self.assertTrue(target_asset.is_file())
            self.assertEqual(target_note.read_text(encoding="utf-8"), "# Lesson\n")
            self.assertEqual(target_asset.read_bytes(), b"image")
            self.assertEqual(result.copied_note_count, 1)
            self.assertEqual(result.copied_asset_count, 1)

    def test_apply_with_overwrite_can_backup_existing_targets_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, target_note, target_asset = _write_plan(root)
            backup_dir = root / "backup"
            target_note.parent.mkdir(parents=True)
            target_note.write_text("existing note", encoding="utf-8")
            target_asset.parent.mkdir(parents=True)
            target_asset.write_bytes(b"existing image")

            result = publish_from_plan(
                plan_path=plan_path,
                apply=True,
                confirm_plan_id="plan-001",
                overwrite=True,
                backup_existing=True,
                backup_dir=backup_dir,
            )

            self.assertEqual(result.status, "applied")
            self.assertEqual(result.backed_up_note_count, 1)
            self.assertEqual(result.backed_up_asset_count, 1)
            self.assertEqual(target_note.read_text(encoding="utf-8"), "# Lesson\n")
            self.assertEqual(target_asset.read_bytes(), b"image")

            payload = json.loads(result.result_json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["backup_existing"], True)
            self.assertEqual(payload["backup_dir"], str(backup_dir))
            self.assertEqual(payload["backed_up_note_count"], 1)
            self.assertEqual(payload["backed_up_asset_count"], 1)
            note_backup = Path(payload["backed_up_notes"][0]["backup"])
            asset_backup = Path(payload["backed_up_assets"][0]["backup"])
            self.assertEqual(note_backup.read_text(encoding="utf-8"), "existing note")
            self.assertEqual(asset_backup.read_bytes(), b"existing image")
            self.assertTrue((backup_dir / "publication-backup.json").is_file())
            self.assertTrue((backup_dir / "publication-backup.md").is_file())

    def test_rejects_apply_without_matching_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, _, _ = _write_plan(root)

            with self.assertRaises(ValueError):
                publish_from_plan(
                    plan_path=plan_path,
                    apply=True,
                    confirm_plan_id="wrong-plan",
                    overwrite=False,
                )

    def test_rejects_existing_target_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, target_note, _ = _write_plan(root)
            target_note.parent.mkdir(parents=True)
            target_note.write_text("existing", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                publish_from_plan(
                    plan_path=plan_path,
                    apply=True,
                    confirm_plan_id="plan-001",
                    overwrite=False,
                )

    def test_conflict_report_classifies_existing_target_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path, target_note, target_asset = _write_plan(root)
            target_note.parent.mkdir(parents=True)
            target_note.write_text("existing", encoding="utf-8")
            target_asset.parent.mkdir(parents=True)
            target_asset.write_bytes(b"image")

            report = create_publication_conflict_report(plan_path=plan_path)

            self.assertEqual(report.status, "conflicts_detected")
            self.assertEqual(report.note_conflict_count, 1)
            self.assertEqual(report.asset_conflict_count, 1)
            self.assertTrue(report.json_path.is_file())
            self.assertTrue(report.markdown_path.is_file())

            payload = json.loads(report.json_path.read_text(encoding="utf-8"))
            item = payload["items"][0]
            self.assertEqual(item["note"]["target_state"], "exists")
            self.assertEqual(item["note"]["hash_state"], "different")
            self.assertEqual(item["note"]["planned_action_without_overwrite"], "block")
            self.assertEqual(item["note"]["planned_action_with_overwrite"], "overwrite")
            self.assertEqual(item["assets"][0]["target_state"], "exists")
            self.assertEqual(item["assets"][0]["hash_state"], "same")
            self.assertEqual(item["assets"][0]["planned_action_without_overwrite"], "skip_same")
            self.assertEqual(item["assets"][0]["planned_action_with_overwrite"], "skip_same")
            self.assertIn(
                "Vault Publication Conflicts",
                report.markdown_path.read_text(encoding="utf-8"),
            )


def _write_plan(root: Path) -> tuple[Path, Path, Path]:
    source_note = root / "experiment" / "renders" / "route" / "baseline" / "Lesson" / "note.md"
    source_asset = (
        root
        / "experiment"
        / "renders"
        / "route"
        / "baseline"
        / "Lesson"
        / "assets"
        / "Lesson"
        / "frame_000001.jpg"
    )
    target_root = root / "vault" / "20_Learning" / "vbook" / "Course"
    target_note = target_root / "Lesson.md"
    target_asset = target_root / "assets" / "Lesson" / "frame_000001.jpg"
    plan_path = root / "experiment" / "publication-plans" / "plan-001" / "publication-plan.json"

    source_note.parent.mkdir(parents=True, exist_ok=True)
    source_note.write_text("# Lesson\n", encoding="utf-8")
    source_asset.parent.mkdir(parents=True, exist_ok=True)
    source_asset.write_bytes(b"image")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kind": "vault_publication_dry_run_plan",
                "plan_id": "plan-001",
                "dry_run": True,
                "target_vault_root": str(target_root),
                "item_count": 1,
                "total_asset_count": 1,
                "total_missing_image_count": 0,
                "items": [
                    {
                        "lesson": "Lesson",
                        "source_note": str(source_note),
                        "target_note": str(target_note),
                        "asset_count": 1,
                        "missing_image_count": 0,
                        "assets": [
                            {
                                "source": str(source_asset),
                                "target": str(target_asset),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return plan_path, target_note, target_asset


if __name__ == "__main__":
    unittest.main()
