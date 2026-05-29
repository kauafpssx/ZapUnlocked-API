#!/usr/bin/env python3
"""Minimal wheel installer — baixa uma wheel e extrai no target.

Uso: python3 install_wheel.py <wheel_url> <target>
"""

import shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path


def _rename_extensions(target: Path) -> None:
    """Renomeia .so da wheel para {module}.so.

    As wheels nomeiam extensões nativas com tags de plataforma
    (ex: _pydantic_core.cp313-cp313-manylinux_2_17_x86_64.so), mas o
    interpretador só reconhece sufixos como .cpython-313-x86_64-linux-gnu.so
    ou .so genérico.  Limpamos os tags e deixamos apenas {module}.so, que
    está sempre em EXTENSION_SUFFIXES.
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
        print('    extraido', file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
