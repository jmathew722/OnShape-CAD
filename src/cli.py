"""Command-line interface for safe, read-only Onshape inspection."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .inventory import (
    assembly_summary,
    element_kind,
    find_element,
    list_connectors,
    list_instances,
    list_mates,
    summarize_elements,
)
from .onshape_client import OnshapeClient, OnshapeError


ID_RE = re.compile(r"^[0-9a-f]{24}$", re.IGNORECASE)
DEFAULT_DOCUMENT_ID = "944558403f04d7842312d8f6"
DEFAULT_WORKSPACE_ID = "0e2895e7580dcc7747665856"
DEFAULT_ELEMENT_ID = "abbe646800a37a61d13f6efc"
PROJECT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class Target:
    document_id: str
    workspace_id: str
    element_id: str
    api_version: str

    @classmethod
    def from_environment(cls) -> "Target":
        target = cls(
            document_id=os.environ.get("ONSHAPE_DOCUMENT_ID", DEFAULT_DOCUMENT_ID),
            workspace_id=os.environ.get("ONSHAPE_WORKSPACE_ID", DEFAULT_WORKSPACE_ID),
            element_id=os.environ.get("ONSHAPE_ELEMENT_ID", DEFAULT_ELEMENT_ID),
            api_version=os.environ.get("ONSHAPE_API_VERSION", "v13"),
        )
        for label, value in (
            ("ONSHAPE_DOCUMENT_ID", target.document_id),
            ("ONSHAPE_WORKSPACE_ID", target.workspace_id),
            ("ONSHAPE_ELEMENT_ID", target.element_id),
        ):
            if not ID_RE.fullmatch(value):
                raise ValueError(f"{label} must be a 24-character hexadecimal Onshape ID")
        if not re.fullmatch(r"v[0-9]+", target.api_version):
            raise ValueError("ONSHAPE_API_VERSION must look like v13")
        return target


def _elements(client: OnshapeClient, target: Target) -> list[dict[str, Any]]:
    payload = client.get(
        f"/api/{target.api_version}/documents/d/{target.document_id}/w/{target.workspace_id}/elements"
    )
    if not isinstance(payload, list):
        raise OnshapeError("Element-list response did not have the expected JSON array shape")
    return payload


def _assert_assembly(client: OnshapeClient, target: Target) -> dict[str, Any]:
    elements = _elements(client, target)
    element = find_element(elements, target.element_id)
    if element is None:
        raise OnshapeError("Configured element was not found in the configured document workspace")
    kind = element_kind(element)
    if "ASSEMBLY" not in kind:
        raise OnshapeError(f"Configured element is {kind}, not an Assembly; assembly inspection stopped")
    return element


def _assembly(client: OnshapeClient, target: Target) -> dict[str, Any]:
    _assert_assembly(client, target)
    payload = client.get(
        f"/api/{target.api_version}/assemblies/d/{target.document_id}/w/{target.workspace_id}/e/{target.element_id}",
        params={
            "includeMateFeatures": "true",
            "includeMateConnectors": "true",
            "includeNonSolids": "true",
            "excludeSuppressed": "false",
        },
    )
    if not isinstance(payload, dict) or "rootAssembly" not in payload:
        raise OnshapeError("Assembly response did not contain rootAssembly")
    return payload


def run(command: str, client: OnshapeClient, target: Target) -> dict[str, Any]:
    if command == "inspect-document":
        document = client.get(f"/api/{target.api_version}/documents/{target.document_id}")
        elements = _elements(client, target)
        selected = find_element(elements, target.element_id)
        return {
            "document": {"id": target.document_id, "name": document.get("name")},
            "workspace_id": target.workspace_id,
            "configured_element": summarize_elements([selected])[0] if selected else None,
            "elements": summarize_elements(elements),
            "status": "PASS" if selected else "FAIL",
            "read_only": True,
        }

    payload = _assembly(client, target)
    if command == "inspect-assembly":
        result = assembly_summary(payload)
    elif command == "list-instances":
        result = {"instances": list_instances(payload)}
    elif command == "list-mates":
        result = {"mates": list_mates(payload)}
    elif command == "list-connectors":
        result = {"mate_connectors": list_connectors(payload)}
    else:
        raise ValueError(f"Unknown command: {command}")
    return {
        "document_id": target.document_id,
        "workspace_id": target.workspace_id,
        "element_id": target.element_id,
        "status": "PASS",
        "read_only": True,
        **result,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "command",
        choices=("inspect-document", "inspect-assembly", "list-instances", "list-mates", "list-connectors"),
    )
    result.add_argument("--compact", action="store_true", help="emit compact JSON")
    return result


def main(argv: list[str] | None = None) -> int:
    # Never search parent directories: they may contain unrelated or revoked keys.
    load_dotenv(dotenv_path=PROJECT_ENV_FILE)
    args = parser().parse_args(argv)
    try:
        target = Target.from_environment()
        result = run(args.command, OnshapeClient(), target)
    except (OnshapeError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc), "read_only": True}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0
