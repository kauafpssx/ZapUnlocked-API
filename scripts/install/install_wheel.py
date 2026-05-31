#!/usr/bin/env python3
"""Minimal wheel installer — downloads a wheel and extracts to target.

Usage: python3 install_wheel.py <wheel_url> <target>
"""

import shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path


def _rename_extensions(target: Path) -> None:
    """Renames .so files from wheel to {module}.so.

    Wheels name native extensions with platform tags
    (e.g., _pydantic_core.cp313-cp313-manylinux_2_17_x86_64.so), but the
    interpreter only recognizes suffixes like .cpython-313-x86_64-linux-gnu.so
    or plain .so. We strip the tags and keep only {module}.so, which
    is always in EXTENSION_SUFFIXES.
    """
    for so in target.rglob('*.so'):
        mod = so.stem.split('.')[0]
        bare = so.with_name(mod + '.so')
        if so != bare:
            so.rename(bare)


def main():
    url, target = sys.argv[1], Path(sys.argv[2])
    target.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    try:
        whl = tmp / url.rsplit('/', 1)[-1]
        urllib.request.urlretrieve(url, whl)
        with zipfile.ZipFile(whl) as zf:
            zf.extractall(target)
        _rename_extensions(target)
        print('    extracted', file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
