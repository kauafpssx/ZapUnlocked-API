"""
Backward-compatible shim — redirects to src.utils.parsing.message_parser.

This file exists so existing imports continue to work during migration.
New code should import from src.utils.parsing.message_parser directly.
"""

from src.utils.parsing.message_parser import parse_message, should_ignore_message  # noqa: F401
