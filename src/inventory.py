"""Convert Onshape document and assembly payloads into bounded, auditable summaries."""

from __future__ import annotations

from typing import Any, Iterable


def element_kind(element: dict[str, Any]) -> str:
    value = element.get("elementType") or element.get("type") or "UNKNOWN"
    return str(value).upper()


def summarize_elements(elements: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": element.get("id"),
            "name": element.get("name"),
            "type": element_kind(element),
        }
        for element in elements
    ]


def find_element(elements: Iterable[dict[str, Any]], element_id: str) -> dict[str, Any] | None:
    return next((element for element in elements if element.get("id") == element_id), None)


def _assemblies(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    root = payload.get("rootAssembly") or {}
    yield "root", root
    for index, assembly in enumerate(payload.get("subAssemblies") or []):
        context = assembly.get("fullConfiguration") or assembly.get("elementId") or f"subassembly-{index + 1}"
        yield str(context), assembly


def list_instances(payload: dict[str, Any]) -> list[dict[str, Any]]:
    occurrences = payload.get("occurrences") or []
    occurrence_by_leaf = {
        occurrence.get("path", [None])[-1]: occurrence
        for occurrence in occurrences
        if occurrence.get("path")
    }
    result: list[dict[str, Any]] = []
    for context, assembly in _assemblies(payload):
        for instance in assembly.get("instances") or []:
            occurrence = occurrence_by_leaf.get(instance.get("id"), {}) if context == "root" else {}
            result.append(
                {
                    "assembly": context,
                    "id": instance.get("id"),
                    "name": instance.get("name"),
                    "type": instance.get("type"),
                    "suppressed": instance.get("suppressed", False),
                    "part_id": instance.get("partId"),
                    "document_id": instance.get("documentId"),
                    "element_id": instance.get("elementId"),
                    "fixed": instance.get("isFixed", occurrence.get("fixed")),
                    "occurrence_path": occurrence.get("path"),
                    "transform": occurrence.get("transform"),
                }
            )
    return result


def _features(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    for context, assembly in _assemblies(payload):
        for feature in assembly.get("features") or []:
            yield context, feature


def _feature_summary(context: str, feature: dict[str, Any]) -> dict[str, Any]:
    parameters = feature.get("parameters") or []
    return {
        "assembly": context,
        "id": feature.get("featureId") or feature.get("id"),
        "name": feature.get("name"),
        "feature_type": feature.get("featureType"),
        "bt_type": feature.get("btType"),
        "suppressed": feature.get("suppressed", False),
        "state": feature.get("featureState") or feature.get("state"),
        "parameters": [
            {
                "id": parameter.get("parameterId"),
                "value": parameter.get("value"),
                "queries": parameter.get("queries"),
            }
            for parameter in parameters
            if parameter.get("parameterId") is not None
        ],
    }


def list_mates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for context, feature in _features(payload):
        kind = str(feature.get("featureType") or "").lower()
        bt_type = str(feature.get("btType") or "").lower()
        if kind == "mate" or ("mate" in bt_type and "connector" not in bt_type):
            result.append(_feature_summary(context, feature))
    return result


def list_connectors(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for context, feature in _features(payload):
        kind = str(feature.get("featureType") or "").lower()
        bt_type = str(feature.get("btType") or "").lower()
        if "mateconnector" in kind.replace("_", "") or "mateconnector" in bt_type.replace("_", ""):
            result.append(_feature_summary(context, feature))
    return result


def assembly_summary(payload: dict[str, Any]) -> dict[str, Any]:
    instances = list_instances(payload)
    mates = list_mates(payload)
    connectors = list_connectors(payload)
    return {
        "instances": instances,
        "mates": mates,
        "mate_connectors": connectors,
        "counts": {
            "instances": len(instances),
            "mates": len(mates),
            "mate_connectors": len(connectors),
            "occurrences": len(payload.get("occurrences") or []),
            "subassemblies": len(payload.get("subAssemblies") or []),
        },
    }
