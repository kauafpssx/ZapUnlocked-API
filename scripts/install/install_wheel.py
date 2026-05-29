#!/usr/bin/env python3
"""Lightweight wheel installer — downloads wheels from PyPI and extracts them.

Bypasses pip entirely to avoid OOM on Alwaysdata's 256 MB RAM.
Installs transitive deps by parsing requires_dist from the PyPI JSON API.
"""

import json, re, shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path


def _vt(ver: str):
    parts = re.findall(r'\d+', ver)
    return tuple(int(p) for p in parts[:3])


def _parse_spec(spec: str):
    spec = spec.strip()
    spec = re.sub(r'\[.*?\]', '', spec)
    for op in ('>=', '<=', '!=', '~=', '==', '>', '<'):
        if op in spec:
            pkg, ver = spec.split(op, 1)
            return pkg.strip(), f'{op}{ver.strip()}'
    return spec, ''


def _best_version(data, ver_spec: str) -> str:
    releases = list(data['releases'].keys())
    if not ver_spec:
        return data['info']['version']
    op = re.match(r'[<>=!~]+', ver_spec).group()
    tv = _vt(ver_spec[len(op):])
    matches = []
    for v in releases:
        try:
            vt = _vt(v)
            if (op == '>=' and vt >= tv) or \
               (op == '>' and vt > tv) or \
               (op == '<=' and vt <= tv) or \
               (op == '<' and vt < tv) or \
               (op == '==' and vt == tv) or \
               (op == '!=' and vt != tv):
                matches.append(v)
        except Exception:
            pass
    if not matches:
        return data['info']['version']
    matches.sort(key=_vt)
    return matches[-1]


def _fetch_json(pkg: str):
    url = f'https://pypi.org/pypi/{pkg}/json'
    return json.loads(urllib.request.urlopen(url).read())


def _non_extra_deps(data) -> list:
    """Return list of 'pkg>=ver' specs for non-extras dependencies."""
    rd = data['info'].get('requires_dist') or []
    out = []
    for dep in rd:
        dep = dep.strip()
        # skip extras-only deps
        if 'extra ==' in dep:
            continue
        # strip environment markers after ;
        if ';' in dep:
            dep = dep.split(';')[0].strip()
        out.append(dep)
    return out


def _wheel_url(data, version: str):
    for f in data['urls']:
        if f['packagetype'] == 'bdist_wheel' and f['version'] == version:
            if f['python_version'] in ('py3', 'py2.py3', 'none'):
                return f['url']
    for f in data['urls']:
        if f['packagetype'] == 'bdist_wheel' and f['version'] == version:
            return f['url']
    return None


def _install_wheel(url: str, target: Path) -> None:
    tmp = Path(tempfile.mkdtemp())
    try:
        whl = tmp / url.rsplit('/', 1)[-1]
        urllib.request.urlretrieve(url, whl)
        with zipfile.ZipFile(whl) as zf:
            zf.extractall(target)
        print(f'    extraido para {target}', file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install(pkg_spec: str, target: Path, _seen: set = None) -> bool:
    if _seen is None:
        _seen = set()
    pkg, ver_spec = _parse_spec(pkg_spec)

    if pkg in _seen:
        return True
    _seen.add(pkg)

    # Fetch package info
    try:
        data = _fetch_json(pkg)
    except Exception as e:
        print(f'  ERRO ao buscar {pkg}: {e}', file=sys.stderr)
        return False

    version = _best_version(data, ver_spec)

    # Check if already installed
    dist_dir = target / f'{pkg}-{version}.dist-info'
    if dist_dir.is_dir():
        print(f'  {pkg}=={version}  ja instalado', file=sys.stderr)
        return True

    url = _wheel_url(data, version)
    if not url:
        print(f'  Sem wheel para {pkg} {version}', file=sys.stderr)
        return False

    print(f'  {pkg}=={version}', file=sys.stderr)
    _install_wheel(url, target)

    # Install non-extras deps
    deps = _non_extra_deps(data)
    for dep in deps:
        install(dep, target, _seen)

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Uso: {sys.argv[0]} <pkg_spec> [site_packages]', file=sys.stderr)
        sys.exit(1)
    spec = sys.argv[1]
    if len(sys.argv) >= 3:
        target = Path(sys.argv[2])
    else:
        import site as _site
        try:
            target = Path(_site.getsitepackages()[-1])
        except Exception:
            target = Path([p for p in sys.path if 'site-packages' in p][0])
    ok = install(spec, target)
    sys.exit(0 if ok else 1)
