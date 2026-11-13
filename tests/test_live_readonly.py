import os
import unittest
from pathlib import Path

from dotenv import load_dotenv

from src.cli import Target, run
from src.onshape_client import OnshapeClient


# Match the application: never inherit a dotenv file from a parent project.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
LIVE_ENABLED = (
    os.environ.get("RUN_ONSHAPE_INTEGRATION") == "1"
    and bool(os.environ.get("ONSHAPE_ACCESS_KEY"))
    and bool(os.environ.get("ONSHAPE_SECRET_KEY"))
)


@unittest.skipUnless(LIVE_ENABLED, "fresh live credentials and RUN_ONSHAPE_INTEGRATION=1 are required")
class LiveReadOnlyTests(unittest.TestCase):
    def test_document_and_element_are_accessible(self):
        result = run("inspect-document", OnshapeClient(), Target.from_environment())
        self.assertEqual("PASS", result["status"])
        self.assertTrue(result["read_only"])


if __name__ == "__main__":
    unittest.main()
