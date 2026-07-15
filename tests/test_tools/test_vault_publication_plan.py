import json
import tempfile
import unittest
from pathlib import Path

from tools.vault_publication_plan import create_publication_plan


class VaultPublicationPlanTest(unittest.TestCase):
    def test_creates_dry_run_plan_for_route_renders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            _write_render(
                root,
                route="vtext_first_vault_enhance",
                lesson="如何筛选龙头股？",
                image_name="frame 240.jpg",
            )
            target_root = Path(tmp) / "vault" / "20_Learning" / "vbook" / "投资训练营"

            package = create_publication_plan(
                experiment_root=root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                target_vault_root=target_root,
                plan_id="plan-001",
            )

            manifest = json.loads(package.json_path.read_text(encoding="utf-8"))
            markdown = package.markdown_path.read_text(encoding="utf-8")
            json_exists = package.json_path.is_file()
            markdown_exists = package.markdown_path.is_file()

        self.assertTrue(json_exists)
        self.assertTrue(markdown_exists)
        self.assertEqual(manifest["kind"], "vault_publication_dry_run_plan")
        self.assertTrue(manifest["dry_run"])
        self.assertEqual(manifest["item_count"], 1)
        self.assertEqual(manifest["total_asset_count"], 1)
        self.assertEqual(manifest["total_missing_image_count"], 0)
        item = manifest["items"][0]
        self.assertEqual(item["lesson"], "如何筛选龙头股？")
        self.assertTrue(item["target_note"].endswith("如何筛选龙头股？.md"))
        self.assertTrue(item["target_assets_dir"].endswith("assets\\如何筛选龙头股？") or item["target_assets_dir"].endswith("assets/如何筛选龙头股？"))
        self.assertEqual(item["markdown_image_count"], 1)
        self.assertIn("vault_write: disabled", markdown)
        self.assertIn("如何筛选龙头股？.md", markdown)

    def test_reports_missing_markdown_image_without_copying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            note = (
                root
                / "renders"
                / "vtext_first_vault_enhance"
                / "baseline"
                / "Missing Asset"
                / "note.md"
            )
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text("# Missing Asset\n\n![x](assets/Missing%20Asset/nope.jpg)\n", encoding="utf-8")

            package = create_publication_plan(
                experiment_root=root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                target_vault_root=Path(tmp) / "vault" / "20_Learning" / "vbook",
                plan_id="plan-001",
            )

            manifest = json.loads(package.json_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["total_missing_image_count"], 1)
        self.assertEqual(manifest["items"][0]["missing_image_count"], 1)

    def test_ignores_unreferenced_assets_in_publication_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            _write_render(
                root,
                route="vtext_first_vault_enhance",
                lesson="反抽 反弹 反转",
                image_name="frame_000003.jpg",
            )
            extra = (
                root
                / "renders"
                / "vtext_first_vault_enhance"
                / "baseline"
                / "反抽 反弹 反转"
                / "assets"
                / "反抽 反弹 反转"
                / "frame_000001.jpg"
            )
            extra.write_bytes(b"unused image")

            package = create_publication_plan(
                experiment_root=root,
                route="vtext_first_vault_enhance",
                variant="baseline",
                target_vault_root=Path(tmp) / "vault" / "20_Learning" / "vbook",
                plan_id="plan-001",
            )

            manifest = json.loads(package.json_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["total_asset_count"], 1)
        self.assertEqual(manifest["items"][0]["assets"][0]["source"].endswith("frame_000003.jpg"), True)

    def test_rejects_plan_id_that_escapes_experiment_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "experiment"
            root.mkdir()

            with self.assertRaises(ValueError):
                create_publication_plan(
                    experiment_root=root,
                    route="vtext_first_vault_enhance",
                    variant="baseline",
                    target_vault_root=Path(tmp) / "vault" / "20_Learning" / "vbook",
                    plan_id="../outside",
                )


def _write_render(root: Path, *, route: str, lesson: str, image_name: str) -> None:
    lesson_dir = root / "renders" / route / "baseline" / lesson
    image = lesson_dir / "assets" / lesson / image_name
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"fake image")
    note = lesson_dir / "note.md"
    note.write_text(
        f"# {lesson}\n\n![{lesson}](assets/{lesson.replace(' ', '%20')}/{image_name.replace(' ', '%20')})\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
