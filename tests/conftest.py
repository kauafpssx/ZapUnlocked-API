"""Global test configuration — ensures libmagic is discoverable for neonize imports."""

import os
import pytest

from src.services.whatsapp import state


_libmagic_dir = os.path.join(
    os.path.dirname(__file__),
    "..", ".venv", "Lib", "site-packages", "magic", "libmagic",
)
if os.path.isdir(_libmagic_dir):
    os.environ["PATH"] = _libmagic_dir + os.pathsep + os.environ.get("PATH", "")


@pytest.fixture(autouse=True)
def reset_whatsapp_state():
    """Reset the state singleton after each test to prevent cross-test leakage."""
    yield
    state.reset_for_logout()
