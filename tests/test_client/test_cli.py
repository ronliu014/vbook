import io
import unittest
from contextlib import redirect_stdout

from vbook_client.cli import main


class CliTest(unittest.TestCase):
    def test_version_prints_project_version(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            code = main(["--version"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), "0.1.0")

    def test_check_prints_skeleton_readiness(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            code = main(["check"])

        self.assertEqual(code, 0)
        self.assertIn("vBook skeleton ready", stdout.getvalue())

    def test_production_batch_preview_help_is_available(self) -> None:
        stdout = io.StringIO()

        with self.assertRaises(SystemExit) as ctx, redirect_stdout(stdout):
            main(["production-batch-preview", "--help"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(
            "Run preview-only vtext-first production batch",
            stdout.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
