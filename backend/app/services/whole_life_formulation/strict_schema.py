"""
Convert a Pydantic model's JSON schema into OpenAI Structured Outputs
strict-mode form: every object gets additionalProperties: false and every
property (including nullable ones) is listed in `required`. Pydantic's own
model_json_schema() doesn't do this by default - fields with `Optional[X] =
None`-style defaults are omitted from `required`, and nothing sets
additionalProperties. schema.py avoids default values specifically so every
field is present in Pydantic's own `required` list already; this function's
real job is the recursive additionalProperties: false + $defs patch.
"""
from typing import Any, Dict
from pydantic import BaseModel


def _patch(node: Any) -> Any:
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            node["additionalProperties"] = False
            if "properties" in node:
                node["required"] = list(node["properties"].keys())
        for value in node.values():
            _patch(value)
    elif isinstance(node, list):
        for item in node:
            _patch(item)
    return node


def strict_json_schema(model: type[BaseModel]) -> Dict[str, Any]:
    schema = model.model_json_schema()
    return _patch(schema)
