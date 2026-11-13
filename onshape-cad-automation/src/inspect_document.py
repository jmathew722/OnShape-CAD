"""Inspect metadata for the configured Onshape document (no modifications)."""
import json
import os
from dotenv import load_dotenv
from .onshape_client import OnshapeClient


def main():
    load_dotenv()
    doc = os.environ.get("ONSHAPE_DOCUMENT_ID", "944558403f04d7842312d8f6")
    workspace = os.environ.get("ONSHAPE_WORKSPACE_ID", "0e2895e7580dcc7747665856")
    element = os.environ.get("ONSHAPE_ELEMENT_ID", "abbe646800a37a61d13f6efc")
    client = OnshapeClient()
    result = client.get(f"/api/documents/d/{doc}")
    print(json.dumps({"document_name": result.get("name"), "document_id": doc,
                      "workspace_id": workspace, "element_id": element,
                      "note": "Metadata fetched successfully; element type and mates not yet inspected."}, indent=2))


if __name__ == "__main__":
    main()
