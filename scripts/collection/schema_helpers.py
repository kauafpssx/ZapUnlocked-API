"""Helpers for resolving OpenAPI $refs, generating example values,
and building request bodies from schema definitions.
"""

import json
from typing import Any, Dict, List, Optional

from .config import SKIP_FIELDS, COLLECTION_VARS
from .endpoint_bodies import FIELD_EXAMPLES


def resolve_ref(ref: str, schema: Dict) -> Dict:
    """Resolve a JSON Schema $ref to the actual schema definition."""
    parts = ref.lstrip("#/").split("/")
    current = schema
    for part in parts:
        if part in current:
            current = current[part]
        else:
            return {}
    return current


def get_schema_properties(schema_def: Dict, openapi_schema: Dict) -> Dict:
    """Get resolved properties from a schema definition, following $refs."""
    if "$ref" in schema_def:
        schema_def = resolve_ref(schema_def["$ref"], openapi_schema)
    if "allOf" in schema_def:
        combined = {}
        for sub in schema_def["allOf"]:
            combined.update(get_schema_properties(sub, openapi_schema))
        return combined
    return {k: v for k, v in schema_def.get("properties", {}).items()}


def get_required_fields(schema_def: Dict, openapi_schema: Dict) -> List[str]:
    """Get required fields from a schema definition."""
    if "$ref" in schema_def:
        schema_def = resolve_ref(schema_def["$ref"], openapi_schema)
    if "allOf" in schema_def:
        required = []
        for sub in schema_def["allOf"]:
            required.extend(get_required_fields(sub, openapi_schema))
        return required
    return schema_def.get("required", [])


def generate_example_value(prop: Dict, openapi_schema: Dict, depth: int = 0) -> Any:
    """Generate an example value from a JSON schema property."""
    if depth > 5:
        return "..."

    if "$ref" in prop:
        prop = resolve_ref(prop["$ref"], openapi_schema)

    if "example" in prop:
        return prop["example"]

    if "default" in prop:
        return prop["default"]

    # Use FIELD_EXAMPLES for known field names
    if "properties" not in prop:
        for pattern, example in FIELD_EXAMPLES.items():
            if pattern in str(prop.get("title", "")):
                return example

    prop_type = prop.get("type", "string")

    if prop_type == "string":
        enum = prop.get("enum")
        if enum:
            return enum[0]
        fmt = prop.get("format", "")
        if fmt == "date":
            return "2024-01-01"
        if fmt == "date-time":
            return "2024-01-01T00:00:00Z"
        if fmt == "uri" or fmt == "url":
            return "https://example.com"
        if fmt == "email":
            return "user@example.com"
        if fmt == "phone":
            return "+5511999999999"
        if fmt == "binary":
            return ""
        return "string"

    if prop_type == "integer":
        return prop.get("minimum", 0) or 1

    if prop_type == "number":
        return float(prop.get("minimum", 0) or 0.0)

    if prop_type == "boolean":
        return False

    if prop_type == "array":
        items = prop.get("items", {})
        return [generate_example_value(items, openapi_schema, depth + 1)]

    if prop_type == "object":
        props = prop.get("properties", {})
        obj = {}
        for key, val in props.items():
            if key in SKIP_FIELDS:
                continue
            obj[key] = generate_example_value(val, openapi_schema, depth + 1)
        return obj

    return "unknown"


def generate_request_body(request_body: Dict, openapi_schema: Dict) -> Optional[str]:
    """Generate an example JSON body from an OpenAPI requestBody definition."""
    if not request_body:
        return None

    content = request_body.get("content", {})

    # Prefer application/json
    if "application/json" in content:
        schema_def = content["application/json"].get("schema", {})
    elif "*/*" in content:
        schema_def = content["*/*"].get("schema", {})
    else:
        # Try first available content type
        media_type = list(content.keys())[0] if content else None
        if not media_type:
            return None
        schema_def = content[media_type].get("schema", {})

    props = get_schema_properties(schema_def, openapi_schema)
    required = set(get_required_fields(schema_def, openapi_schema))
    phone_var = "{{PHONE}}"

    # Build example body
    body = {}
    for key, prop in props.items():
        if key in SKIP_FIELDS:
            continue

        # Use phone for phone-related fields
        if key == "phone" or key.endswith("_phone"):
            body[key] = phone_var
        # Use FIELD_EXAMPLES for known names
        elif key in FIELD_EXAMPLES:
            body[key] = FIELD_EXAMPLES[key]
        # Add required fields with example values, skip optional if not needed
        elif key in required:
            body[key] = generate_example_value(prop, openapi_schema)

    if not body:
        return None

    return json.dumps(body, indent=4, ensure_ascii=False)


def get_path_parameters(path: str, operation: Dict, openapi_schema: Dict) -> List[Dict]:
    """Extract URL path parameters and convert to Postman variables."""
    params = []
    for param in operation.get("parameters", []):
        if param.get("in") == "path":
            name = param["name"]
            var_name = name.upper()
            if var_name in [v["key"] for v in COLLECTION_VARS]:
                params.append({"key": f"{{{{{var_name}}}}}", "value": "", "disabled": False})
            else:
                params.append({"key": name, "value": "", "disabled": False})
    return params
