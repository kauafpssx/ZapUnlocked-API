"""Utilities for cleaning JSON input (comments, trailing commas)."""

import re


def clean_json_text(text: str) -> str:
    """Strip // and /* */ comments and trailing commas from JSON text.

    Allows // and /* */ comments in request bodies (useful for Postman inline docs).
    """
    # Remove // comments (unless preceded by : to avoid breaking URLs)
    text = re.sub(r'(?<!:)\s*//.*', '', text)
    # Remove /* */ comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([\]}])', r'\1', text)
    return text.strip()
