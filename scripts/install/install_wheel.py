#!/usr/bin/env python3
"""Minimal wheel installer — baixa uma wheel e extrai no target.

Uso: python3 install_wheel.py <wheel_url> <target>
"""

import shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path


def main():
    url, target = sys.argv[1], Path(sys.argv[2])
    target.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    try:
        whl = tmp / url.rsplit('/', 1)[-1]
        urllib.request.urlretrieve(url, whl)
        with zipfile.ZipFile(whl) as zf:
            zf.extractall(target)
        print('    extraido', file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
