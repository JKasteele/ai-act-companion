"""Fail a release when its tag and public version metadata disagree."""

import json
import pathlib
import re
import sys

import tomllib


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("v"):
        raise SystemExit("usage: check_release_version.py v<version>")

    root = pathlib.Path(__file__).resolve().parent.parent
    tag_version = sys.argv[1][1:]
    with (root / "pyproject.toml").open("rb") as fh:
        package_version = tomllib.load(fh)["project"]["version"]

    runtime_text = (root / "app" / "__init__.py").read_text(encoding="utf-8")
    runtime_match = re.search(r'^__version__ = "([^"]+)"$', runtime_text, re.MULTILINE)
    runtime_version = runtime_match.group(1) if runtime_match else "<missing>"
    plugin_version = json.loads(
        (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]

    versions = {
        "tag": tag_version,
        "package": package_version,
        "runtime": runtime_version,
        "plugin": plugin_version,
    }
    if len(set(versions.values())) != 1:
        raise SystemExit(f"Release version mismatch: {versions}")

    print(f"Release metadata aligned at {tag_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
