"""Ensure no dead Python code accumulates in src/."""

import subprocess
import sys
from pathlib import Path


def test_no_dead_code_at_90_pct_confidence():
    """
    Run vulture at 90% confidence on src/. If it finds anything,
    either the code is truly dead (remove it) or a false positive
    exists (raise the threshold or add an inline # noqa).
    """
    src = str(Path(__file__).resolve().parent.parent / "src")
    result = subprocess.run(
        [sys.executable, "-m", "vulture", src, "--min-confidence", "90"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0 or result.stdout.strip():
        msg = (
            "vulture detected potential dead code at ≥90% confidence:\n"
            f"{result.stdout}"
        )
        if result.stderr:
            msg += f"\nstderr:\n{result.stderr}"
        raise AssertionError(msg)
