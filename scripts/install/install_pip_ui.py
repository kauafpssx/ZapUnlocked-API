import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
venv_python = root / ".venv" / "Scripts" / "python.exe"

G = "\033[38;2;66;194;146m"
R = "\033[0m"


def show_pkg(name, installed):
    key = name.lower()
    if key in installed:
        print(f"  {G}\u2713{R} {name} ({installed[key]})")
    else:
        print(f"  {G}\u2713{R} {name} (?)")


r = subprocess.run(
    [str(venv_python), "-m", "pip", "list", "--format=json"],
    capture_output=True,
    text=True,
)
installed = {p["name"].lower(): p["version"] for p in json.loads(r.stdout)}

if len(sys.argv) > 1 and sys.argv[1] == "--magic":
    show_pkg("python-magic-bin", installed)
else:
    reqs = []
    for line in (root / "requirements.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "-", "git+", ".")):
            continue
        name = re.split(r"[>=<\[~!]", line)[0].strip()
        if name:
            reqs.append(name)
    for p in reqs:
        show_pkg(p, installed)
