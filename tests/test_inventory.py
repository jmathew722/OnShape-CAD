import unittest

from src.inventory import assembly_summary, element_kind, find_element


ASSEMBLY = {
    "rootAssembly": {
        "instances": [
            {
                "id": "part-one",
                "name": "Shaft <1>",
                "type": "Part",
                "suppressed": False,
                "partId": "part-id",
                "documentId": "doc-id",
                "elementId": "studio-id",
            }
        ],
        "features": [
            {
                "featureId": "mate-one",
                "name": "Revolute 1",
                "featureType": "mate",
                "btType": "BTMMate-64",
                "parameters": [
                    {"parameterId": "mateType", "value": "REVOLUTE"},
                    {"parameterId": "entities", "queries": [{"queryType": "MATE_CONNECTOR"}]},
                ],
            },
            {
                "featureId": "connector-one",
                "name": "Mate connector 1",
                "featureType": "mateConnector",
                "btType": "BTMMateConnector-66",
                "parameters": [],
            },
        ],
        "occurrences": [
            {
                "path": ["part-one"],
                "fixed": True,
                "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            }
        ],
    },
    "subAssemblies": [],
}


class InventoryTests(unittest.TestCase):
    def test_element_helpers_accept_current_element_type_field(self):
        elements = [{"id": "one", "elementType": "ASSEMBLY"}]
        self.assertEqual("ASSEMBLY", element_kind(elements[0]))
        self.assertIs(elements[0], find_element(elements, "one"))
        self.assertIsNone(find_element(elements, "missing"))

    def test_assembly_summary_separates_mates_and_connectors(self):
        result = assembly_summary(ASSEMBLY)
        self.assertEqual(1, result["counts"]["instances"])
        self.assertEqual(1, result["counts"]["mates"])
        self.assertEqual(1, result["counts"]["mate_connectors"])
        self.assertEqual("REVOLUTE", result["mates"][0]["parameters"][0]["value"])
        self.assertTrue(result["instances"][0]["fixed"])
        self.assertEqual(["part-one"], result["instances"][0]["occurrence_path"])


if __name__ == "__main__":
    unittest.main()
