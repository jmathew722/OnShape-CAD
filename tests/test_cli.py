import os
import unittest
from unittest.mock import patch

from src.cli import DEFAULT_DOCUMENT_ID, DEFAULT_ELEMENT_ID, DEFAULT_WORKSPACE_ID, Target, run
from src.onshape_client import OnshapeError


class StubClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return self.responses.pop(0)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.target = Target(DEFAULT_DOCUMENT_ID, DEFAULT_WORKSPACE_ID, DEFAULT_ELEMENT_ID, "v13")

    def test_target_defaults_are_valid(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.target, Target.from_environment())

    def test_inspect_document_confirms_target_element(self):
        client = StubClient(
            [
                {"name": "Fixture"},
                [{"id": DEFAULT_ELEMENT_ID, "name": "Assembly 1", "elementType": "ASSEMBLY"}],
            ]
        )
        result = run("inspect-document", client, self.target)
        self.assertEqual("PASS", result["status"])
        self.assertEqual("ASSEMBLY", result["configured_element"]["type"])

    def test_assembly_command_stops_when_element_is_not_assembly(self):
        client = StubClient(
            [[{"id": DEFAULT_ELEMENT_ID, "name": "Part Studio 1", "elementType": "PARTSTUDIO"}]]
        )
        with self.assertRaisesRegex(OnshapeError, "not an Assembly"):
            run("inspect-assembly", client, self.target)
        self.assertEqual(1, len(client.calls))


if __name__ == "__main__":
    unittest.main()
