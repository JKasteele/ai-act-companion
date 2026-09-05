"""Build a static guided preview from the same case and actual Python engine.

Run from the repository root: python scripts/build_workspace.py
No model calls, credentials, user data, or backend code enter dist/.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.workspace.case import get_case  # noqa: E402
from app.workspace.routes import scenario_assessment  # noqa: E402


def build():
    public = ROOT / "static/workspace"
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    # Deliberate allowlist: never copy .env, data/, server code, or credentials.
    for name in ("index.html", "workspace.css", "workspace.js", "model.mjs", "favicon.svg"):
        shutil.copy2(public / name, out / name)
    for directory in (public, out):
        (directory / "case.json").write_text(
            json.dumps(get_case(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        (directory / "assessment.json").write_text(
            json.dumps(scenario_assessment(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
    (out / "mode.json").write_text('{"static":true}\n', encoding="utf-8")
    (public / "mode.json").write_text('{"static":false}\n', encoding="utf-8")
    print("Built guided workspace in dist/ from the curated case and deterministic engine.")


if __name__ == "__main__":
    build()
