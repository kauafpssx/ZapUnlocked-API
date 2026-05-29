#!/usr/bin/env python3
"""Lightweight wheel installer — downloads wheels from PyPI and extracts them.

Bypasses pip entirely to avoid OOM on Alwaysdata's 256 MB RAM.
Installs transitive deps by parsing requires_dist from the PyPI JSON API.
"""

import gc, json, re, shutil, sys, tempfile, urllib.request, zipfile
from pathlib import Path


def _vt(ver: str):
    parts = re.findall(r'\d+', ver)
    return tuple(int(p) for p in parts[:3])


def _parse_spec(spec: str):
    spec = spec.strip()
    spec = re.sub(r'\[.*?\]', '', spec)
    m = re.match(r'([a-zA-Z0-9][a-zA-Z0-9._-]*)(.*)', spec)
    if not m:
        return spec, ''
    return m.group(1), m.group(2).strip()


def _matches(v: str, constraint: str) -> bool:
    """Check if version v matches a PEP 440 constraint like '>=1.0,<2.0'."""
    vt = _vt(v)
    for clause in constraint.split(','):
        clause = clause.strip()
        if not clause:
            continue
        op = re.match(r'[<>=!~]+', clause)
        if not op:
            continue
        op = op.group()
        tv = _vt(clause[len(op):])
        try:
            if op == '>=' and not (vt >= tv): return False
            if op == '>' and not (vt > tv): return False
            if op == '<=' and not (vt <= tv): return False
            if op == '<' and not (vt < tv): return False
            if op == '==' and not (vt == tv): return False
            if op == '!=' and not (vt != tv): return False
        except Exception:
            return False
    return True


def _best_version(data, ver_spec: str) -> str:
    releases = list(data['releases'].keys())
    if not ver_spec:
        return data['info']['version']
    matches = [v for v in releases if _matches(v, ver_spec)]
    if not matches:
        return data['info']['version']
    matches.sort(key=_vt)
    return matches[-1]


def _fetch_json(pkg: str):
    url = f'https://pypi.org/pypi/{pkg}/json'
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def _non_extra_deps(data) -> list:
    rd = data['info'].get('requires_dist') or []
    out = []
    for dep in rd:
        dep = dep.strip()
        if 'extra ==' in dep:
            continue
        if ';' in dep:
            dep = dep.split(';')[0].strip()
        out.append(dep)
    return out


def _wheel_url(data, version: str):
    for f in data.get('urls') or []:
        if f.get('packagetype') == 'bdist_wheel' and f.get('version') == version:
            if f.get('python_version', '') in ('py3', 'py2.py3', 'none', ''):
                return f['url']
    for f in data.get('releases', {}).get(version, []):
        if f.get('packagetype') == 'bdist_wheel':
            if f.get('python_version', '') in ('py3', 'py2.py3', 'none', ''):
                return f['url']
    for f in data.get('urls') or []:
        if f.get('packagetype') == 'bdist_wheel' and f.get('version') == version:
            return f['url']
    for f in data.get('releases', {}).get(version, []):
        if f.get('packagetype') == 'bdist_wheel':
            return f['url']
    return None


def _install_wheel(url: str, target: Path) -> None:
    tmp = Path(tempfile.mkdtemp())
    try:
        whl = tmp / url.rsplit('/', 1)[-1]
        urllib.request.urlretrieve(url, whl)
        with zipfile.ZipFile(whl) as zf:
            zf.extractall(target)
        print(f'    extraido', file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install(pkg_spec: str, target: Path, _seen: set = None) -> bool:
    if _seen is None:
        _seen = set()
    pkg, ver_spec = _parse_spec(pkg_spec)
    if pkg in _seen:
        return True
    _seen.add(pkg)

    try:
        data = _fetch_json(pkg)
    except Exception as e:
        print(f'  ERRO ao buscar {pkg}: {e}', file=sys.stderr)
        return False

    version = _best_version(data, ver_spec)

    dist_dir = target / f'{pkg}-{version}.dist-info'
    if dist_dir.is_dir():
        print(f'  {pkg}=={version}  ja instalado', file=sys.stderr)
        return True

    deps = _non_extra_deps(data)
    url = _wheel_url(data, version)
    del data  # libera JSON

    if not url:
        print(f'  Sem wheel para {pkg} {version}', file=sys.stderr)
        return False

    target.mkdir(parents=True, exist_ok=True)

    # Instala deps PRIMEIRO — se morrer, o pkg principal nao fica "half-installed"
    for dep in deps:
        if not install(dep, target, _seen):
            print(f'    AVISO: dependencia {dep} falhou', file=sys.stderr)
        gc.collect()

    print(f'  {pkg}=={version}', file=sys.stderr)
    _install_wheel(url, target)
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
