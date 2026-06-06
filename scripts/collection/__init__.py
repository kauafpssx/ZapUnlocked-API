"""Collection Generator Package — modular Postman/Insomnia collection builder.

Modules:
  config.py          — Shared constants, UI helpers, collection variables
  folder_map.py      — URL prefix → folder structure mapping
  endpoint_bodies.py — Realistic example request bodies per endpoint
  descriptions.py    — Manual + auto-generated endpoint descriptions (English)
  schema_helpers.py  — OpenAPI $ref resolution, example value generation
  generator.py       — Core collection builder and CLI entry point
"""
