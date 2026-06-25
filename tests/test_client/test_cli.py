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


if __name__ == "__main__":
    unittest.main()
