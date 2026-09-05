"""Build the complete workspace with the original Python engine for the browser.

Run from the repository root: python scripts/build_workspace.py
No model calls, credentials, user data, API, storage, or provider modules enter dist/.
"""

import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.workspace.case import get_case  # noqa: E402
from app.workspace.routes import scenario_assessment  # noqa: E402
from app.workspace.toolkit import catalogue  # noqa: E402


def build():
    public = ROOT / "static/workspace"
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    # Deliberate allowlist: never copy .env, data/, server code, or credentials.
    for name in ("index.html", "case.html", "workspace.css", "workspace.js", "model.mjs", "favicon.svg",
                 "hub.css", "hub.js", "hub-model.mjs", "casework.mjs", "casework-model.mjs", "engine-worker.mjs", "engine-client.mjs", "markdown.mjs"):
        shutil.copy2(public / name, out / name)
    (out / "notices").mkdir(exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    shutil.copy2(public / "assets/about-context.png", out / "assets/about-context.png")
    for name in ("README.md", "PYODIDE-LICENSE.txt", "PYTHON-LICENSE.txt"):
        shutil.copy2(public / "notices" / name, out / "notices" / name)
    for directory in (public, out):
        (directory / "case.json").write_text(
            json.dumps(get_case(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        (directory / "assessment.json").write_text(
            json.dumps(scenario_assessment(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        (directory / "catalogue.json").write_text(
            json.dumps(catalogue(), ensure_ascii=False) + "\n", encoding="utf-8",
        )
    # Include only the pure, public engine modules; never API/provider/storage code.
    modules = ["__init__", "_normalize", "classifier", "controls", "data_security", "forensics",
               "governance", "i18n", "incident", "modelcard", "questionnaire", "redteam", "reports",
               "security", "stride"]
    sources = [ROOT / "app" / f"{name}.py" for name in modules]
    sources += sorted((ROOT / "app/knowledge").glob("*.py"))
    sources += [ROOT / "app/workspace" / name for name in ("__init__.py", "toolkit.py", "scenarios.py", "case.py")]
    sources += [ROOT / "examples" / f"{e['id']}.json" for e in catalogue()["examples"]]
    with zipfile.ZipFile(out / "engine.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for source in sources:
            info = zipfile.ZipInfo(source.relative_to(ROOT).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    shutil.copy2(out / "engine.zip", public / "engine.zip")
    runtime = ROOT / "node_modules/pyodide"
    runtime_files = ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
    if not all((runtime / name).exists() for name in runtime_files):
        raise RuntimeError("Run npm ci to install the pinned browser Python runtime before building.")
    for directory in (public, out):
        (directory / "runtime").mkdir(exist_ok=True)
        for name in runtime_files:
            shutil.copy2(runtime / name, directory / "runtime" / name)
    (out / "mode.json").write_text('{"static":true}\n', encoding="utf-8")
    (public / "mode.json").write_text('{"static":false}\n', encoding="utf-8")
    print("Built the complete workspace and browser Python engine in dist/.")


if __name__ == "__main__":
    build()
