"""Core collection builder — parses OpenAPI schema and produces Postman v2.1 JSON."""

import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

from .config import (
    PROJECT_ROOT, OUTPUT_FILE,
    COLLECTION_VARS, SKIP_FIELDS,
    _PURPLE, _GREEN, _YELLOW, _GRAY, _WHITE, _RESET,
    ui_banner, ui_tags, ui_sep, ui_task,
    ui_info, ui_ok, ui_warn, ui_err, ui_step, ui_footer,
)
from .folder_map import find_folder
from .endpoint_bodies import ENDPOINT_BODIES
from .descriptions import ENDPOINT_DESCRIPTIONS, auto_generate_description
from .schema_helpers import (
    resolve_ref, get_schema_properties, generate_example_value,
    generate_request_body, get_path_parameters,
)


def build_collection(openapi_schema: Dict) -> Dict:
    """Build the Postman v2.1 collection from the OpenAPI schema."""
    paths = openapi_schema.get("paths", {})
    info = openapi_schema.get("info", {})

    collection: Dict = OrderedDict([
        ("info", OrderedDict([
            ("name", f"{info.get('title', 'API')} (auto-generated)"),
            ("schema", "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"),
            ("description", f"Auto-generated from OpenAPI. Base URL: http://localhost:{os.getenv('PORT', '8300')}"),
        ])),
        ("variable", COLLECTION_VARS),
        ("item", []),
    ])

    # ── Build folder tree ────────────────────────────────────────────────
    folder_tree: Dict = {}

    def ensure_folder(path_parts: List[str]) -> Dict:
        current = folder_tree
        for part in path_parts:
            if part not in current:
                current[part] = {"_items": []}
            current = current[part]
        return current

    total_ops = 0
    total_paths = len(paths)

    # ── Process each path/operation ──────────────────────────────────────
    for url_path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            method = method.upper()
            if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                continue

            total_ops += 1
            summary = operation.get("summary", "") or url_path
            has_security = bool(operation.get("security"))

            # Build request URL (replace path params with Postman variables)
            postman_path_parts = []
            for segment in url_path.strip("/").split("/"):
                if segment.startswith("{") and segment.endswith("}"):
                    var_name = segment[1:-1].upper()
                    if var_name in [v["key"] for v in COLLECTION_VARS]:
                        postman_path_parts.append(f"{{{{{var_name}}}}}")
                    else:
                        postman_path_parts.append(f":{segment[1:-1]}")
                elif segment:
                    postman_path_parts.append(segment)

            raw_url = "{{BASE_URL}}/" + "/".join(postman_path_parts) if postman_path_parts else "{{BASE_URL}}/"

            # ── Extract query parameters ──────────────────────────────────
            query_params = []
            for param in operation.get("parameters", []):
                if param.get("in") == "query":
                    schema = param.get("schema", {})
                    default = schema.get("default", "")
                    query_params.append({
                        "key": param["name"],
                        "value": str(default) if default else "",
                        "description": param.get("description", ""),
                    })

            # ── Headers ──────────────────────────────────────────────────
            headers = []
            if method in ("POST", "PUT"):
                headers.append({"key": "Content-Type", "value": "application/json"})
            if has_security:
                headers.append({"key": "x-api-key", "value": "{{API_KEY}}"})

            # ── Request body ──────────────────────────────────────────────
            body = None
            if url_path in ENDPOINT_BODIES:
                body_data = dict(ENDPOINT_BODIES[url_path])
                commented = body_data.pop("__commented__", {})
                inline_comments = body_data.pop("__inline_comments__", {})
                if body_data.pop("__formdata__", False):
                    file_field = body_data.pop("__file_field__", "file")
                    formdata = []
                    for key, val in body_data.items():
                        is_optional = key != "phone"
                        formdata.append({
                            "key": key,
                            "value": str(val).lower() if isinstance(val, bool) else str(val),
                            "type": "text",
                            "disabled": is_optional,
                        })
                    formdata.insert(0, {
                        "key": file_field,
                        "value": "",
                        "type": "file",
                        "src": [],
                        "disabled": True,
                    })
                    body = {"mode": "formdata", "formdata": formdata}
                else:
                    if commented or inline_comments:
                        # Build active JSON fields, then append // comments
                        active_json = json.dumps(body_data, indent=4, ensure_ascii=False)
                        lines = active_json.rstrip().split('\n')
                        # Remove trailing "}" — we'll re-add after comments
                        if lines[-1].strip() == '}':
                            body_lines = lines[:-1]
                        else:
                            body_lines = lines
                        # Add inline comments on active field lines
                        if inline_comments:
                            for field, comment in inline_comments.items():
                                for i, line in enumerate(body_lines):
                                    stripped = line.strip()
                                    if stripped.startswith(f'"{field}"'):
                                        if stripped.endswith(','):
                                            body_lines[i] = line.rstrip() + ' ' + comment
                                        else:
                                            body_lines[i] = line.rstrip() + ', ' + comment
                                        break
                        # Append commented optional fields
                        for key, val_str in commented.items():
                            body_lines.append(f'    // "{key}": {val_str}')
                        body_lines.append('}')
                        raw_body = '\n'.join(body_lines)
                    else:
                        raw_body = json.dumps(body_data, indent=4, ensure_ascii=False)
                    body = {
                        "mode": "raw",
                        "raw": raw_body,
                        "options": {"raw": {"language": "json"}},
                    }
            elif "requestBody" in operation:
                content_map = operation["requestBody"].get("content", {})
                if "multipart/form-data" in content_map:
                    form_fields = {"phone": "{{PHONE}}"}
                    props = content_map["multipart/form-data"].get("schema", {}).get("properties", {})
                    for key, prop in props.items():
                        if key == "file" or prop.get("format") == "binary":
                            continue
                        if "default" in prop:
                            form_fields[key] = prop["default"]
                    formdata = [{"key": k, "value": str(v), "type": "text", "disabled": k != "phone"} for k, v in form_fields.items()]
                    formdata.insert(0, {"key": "file", "value": "", "type": "file", "src": [], "disabled": True})
                    body = {"mode": "formdata", "formdata": formdata}
                else:
                    body_text = generate_request_body(operation["requestBody"], openapi_schema)
                    if body_text:
                        body = {
                            "mode": "raw",
                            "raw": body_text,
                            "options": {"raw": {"language": "json"}},
                        }

            # ── Build URL dict ───────────────────────────────────────────
            url_dict = OrderedDict([
                ("raw", raw_url),
                ("host", ["{{BASE_URL}}"]),
                ("path", postman_path_parts or [""]),
            ])
            if query_params:
                url_dict["query"] = query_params

            # ── Build request item ────────────────────────────────────────
            request_item = OrderedDict([
                ("name", summary or url_path),
                ("request", OrderedDict([
                    ("method", method),
                    ("url", url_dict),
                ])),
            ])

            if headers:
                request_item["request"]["header"] = headers
            if body:
                request_item["request"]["body"] = body

            # ── Inject description ────────────────────────────────────────
            desc_key = f"{method} {url_path}"
            description = (
                ENDPOINT_DESCRIPTIONS.get(desc_key)
                or ENDPOINT_DESCRIPTIONS.get(url_path)
            )
            if not description:
                # Auto-generate from OpenAPI metadata
                description = auto_generate_description(method, url_path, summary, operation)
            if description:
                request_item["request"]["description"] = description

            # ── Place in folder tree ─────────────────────────────────────
            folder_parts = find_folder(url_path)
            if folder_parts:
                parent = ensure_folder(folder_parts)
                parent["_items"].append(request_item)
            else:
                collection["item"].append(request_item)

    # ── Convert folder tree to Postman items ─────────────────────────────
    def build_items(tree: Dict) -> List[Dict]:
        items = []
        for name, content in sorted(tree.items()):
            if name == "_items":
                continue
            sub_items = list(content.get("_items", []))
            child_items = build_items(content)
            sub_items.extend(child_items)
            if sub_items:
                items.append(OrderedDict([
                    ("name", name),
                    ("item", sub_items),
                ]))
        return items

    collection["item"] = build_items(folder_tree)

    # Attach operation count for the caller
    collection["_meta"] = {"total_ops": total_ops, "total_paths": total_paths}
    return collection


def print_folder_tree(collection: Dict, indent: str = "") -> None:
    """Pretty-print the folder structure to stdout."""
    for item in collection.get("item", []):
        if "item" in item:
            folder_name = item["name"]
            print(f"{indent}{_PURPLE}[{folder_name}]{_RESET}" if not indent
                  else f"{indent}{_PURPLE}[{folder_name}]{_RESET}")
            print_folder_tree(item, indent + "  ")
        else:
            req = item.get("request", {})
            method = req.get("method", "GET")
            name = item.get("name", "")
            method_colors = {
                "GET": "\033[38;2;66;194;146m",
                "POST": "\033[38;2;245;158;11m",
                "PUT": "\033[38;2;107;114;128m",
                "DELETE": "\033[38;2;239;68;68m",
                "PATCH": "\033[38;2;107;114;128m",
            }
            mc = method_colors.get(method, "\033[38;2;107;114;128m")
            method_pad = method.ljust(7)
            print(f"{indent}  {mc}{method_pad}{_RESET} {name}")


def main() -> None:
    """Entry point: bootstrap FastAPI app, read OpenAPI schema, generate collection."""
    ui_banner()
    ui_tags("▶", "COLLECTION GENERATOR", "Postman v2.1")
    ui_sep()

    # ── Step 1: Bootstrap ─────────────────────────────────────────────────
    ui_task("Bootstrapping environment")
    ui_info("Calling bootstrap()...")
    try:
        from src.bootstrap import bootstrap
        bootstrap()
        ui_ok("Environment ready")
    except Exception as e:
        ui_err(f"Bootstrap failed: {e}")
        sys.exit(1)

    # ── Step 2: Read OpenAPI schema ───────────────────────────────────────
    ui_task("Reading OpenAPI schema")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from src.app import create_app
        app = create_app()
        openapi_schema = app.openapi()
        paths_count = len(openapi_schema.get("paths", {}))
        ops_count = sum(len(m) for m in openapi_schema.get("paths", {}).values())
        ui_ok(f"Found {ops_count} operations across {paths_count} paths")
    except Exception as e:
        ui_err(f"Failed to read OpenAPI schema: {e}")
        sys.exit(1)

    # ── Step 3: Build collection ──────────────────────────────────────────
    ui_task("Building Postman collection")
    try:
        collection = build_collection(openapi_schema)
        meta = collection.pop("_meta", {})
        total_ops = meta.get("total_ops", 0)
        ui_ok(f"{total_ops} requests organized into {len(collection.get('item', []))} folders")
    except Exception as e:
        ui_err(f"Failed to build collection: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ── Step 4: Save ──────────────────────────────────────────────────────
    ui_task("Saving collection")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        ui_ok(f"Saved to {OUTPUT_FILE}")
    except Exception as e:
        ui_err(f"Failed to save: {e}")
        sys.exit(1)

    # ── Step 5: Print folder structure ────────────────────────────────────
    ui_task("Folder structure")
    print_folder_tree(collection)

    ui_sep()
    ui_footer("Collection generated successfully")


if __name__ == "__main__":
    main()
