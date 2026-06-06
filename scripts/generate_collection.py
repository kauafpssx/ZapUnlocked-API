#!/usr/bin/env python3
"""
Auto-generate Postman/Insomnia collection from FastAPI OpenAPI schema.

Usage:
    python scripts/generate_collection.py

Generates: ZapUnlocked.collection.json (Postman v2.1 format)

This entry point delegates to collection.generator (scripts/collection/).
All configuration, descriptions, and body examples live in scripts/collection/*.py.
"""

import sys
from pathlib import Path

# sys.path[0] = scripts/ dir (where this script lives)
# Add project root so src.* imports work in the generator
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collection.generator import main

if __name__ == "__main__":
    main()
