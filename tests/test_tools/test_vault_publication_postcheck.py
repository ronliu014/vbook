import json
import tempfile
import unittest
from pathlib import Path

from tools.vault_publication_postcheck import run_publication_postcheck


class VaultPublicationPostcheckTest(unittest.TestCase):
    def test_postcheck_passes_when_hashes_and_markdown_images_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(
                root,
                target_image_exists=True,
            )

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "pass")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["hash_match_count"], 2)
            self.assertEqual(payload["hash_mismatch_count"], 0)
            self.assertEqual(payload["markdown_image_link_count"], 1)
            self.assertEqual(payload["missing_markdown_image_count"], 0)

    def test_postcheck_fails_when_target_hash_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(
                root,
                target_image_exists=True,
            )
            target_note = root / "target" / "Lesson.md"
            target_note.write_text("changed\n", encoding="utf-8")

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "fail")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["hash_mismatch_count"], 1)

    def test_postcheck_fails_when_markdown_image_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = _write_publication_result_fixture(
                root,
                target_image_exists=False,
            )

            package = run_publication_postcheck(publication_result_path=result_path)

            self.assertEqual(package.status, "fail")
            payload = json.loads(package.json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["missing_markdown_image_count"], 1)


def _write_publication_result_fixture(
    root: Path,
    *,
    target_image_exists: bool,
) -> Path:
    source = root / "source"
    target = root / "target"
    source.mkdir()
    target.mkdir()
    source_image = source / "frame_000001.jpg"
    target_image = target / "assets" / "Lesson" / "frame_000001.jpg"
    source_note = source / "note.md"
    target_note = target / "Lesson.md"
    source_image.write_bytes(b"image")
    target_image.parent.mkdir(parents=True)
    if target_image_exists:
        target_image.write_bytes(b"image")
    source_note.write_text("![x](assets/Lesson/frame_000001.jpg)\n", encoding="utf-8")
    target_note.write_text("![x](assets/Lesson/frame_000001.jpg)\n", encoding="utf-8")
    result_path = root / "publication-result.json"
    result_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "kind": "vault_publication_result",
                "plan_id": "plan-a",
                "status": "applied",
                "copied_notes": [
                    {"source": str(source_note), "target": str(target_note)}
                ],
                "copied_assets": [
                    {"source": str(source_image), "target": str(target_image)}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return result_path


if __name__ == "__main__":
    unittest.main()
