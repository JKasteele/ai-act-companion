"""JSON file persistence for assessments.

One file per assessment in the `data/` directory. Deliberately simple and
inspectable; suitable for synthetic example data.
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Where assessments are stored. Overridable via AIACT_DATA_DIR (e.g. a writable
# path in a container / Hugging Face Space); defaults to the project's data/.
DATA_DIR = Path(os.environ.get("AIACT_DATA_DIR") or Path(__file__).resolve().parent.parent / "data")


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _slug(text, fallback="assessment"):
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:40] or fallback


def new_id(sys_name=None):
    """Readable, unique id: <slug>-<8 hex>."""
    return f"{_slug(sys_name)}-{uuid.uuid4().hex[:8]}"


def save(assessment):
    """Save an assessment dict atomically. Requires an 'id' field.

    Writes to a temp file in the same directory and os.replace()s it into place,
    so an interrupted write can never leave a half-written (corrupt) record that
    list_all()/load() would then skip or fail on.
    """
    _ensure_dir()
    path = DATA_DIR / f"{assessment['id']}.json"
    tmp = DATA_DIR / f"{assessment['id']}.{uuid.uuid4().hex[:8]}.tmp"
    payload = json.dumps(assessment, ensure_ascii=False, indent=2)
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)  # atomic on POSIX and Windows
    finally:
        if tmp.exists():
            tmp.unlink()
    return path


# Assessment ids are slug-<hex>; reject anything else to prevent path traversal
# when an id arrives from the API / MCP tools.
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def is_valid_id(assessment_id):
    return bool(isinstance(assessment_id, str) and _ID_RE.match(assessment_id))


def load(assessment_id):
    if not is_valid_id(assessment_id):
        return None
    path = DATA_DIR / f"{assessment_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def delete(assessment_id):
    """Delete a stored assessment. Returns True if a file was removed."""
    if not is_valid_id(assessment_id):
        return False
    path = DATA_DIR / f"{assessment_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def load_all():
    """Every stored assessment as a full dict, newest first. Reads each file
    once — callers that need both the summary and the full record (e.g. the
    portfolio roll-up) should use this instead of list_all() + load() per id."""
    _ensure_dir()
    out = []
    for path in DATA_DIR.glob("*.json"):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    out.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return out


def summarise(data, fallback_id=""):
    """Short summary row for one full assessment dict."""
    cls = data.get("classification", {})
    security = data.get("security") or {}
    return {
        "id": data.get("id", fallback_id),
        "sys_name": data.get("answers", {}).get("sys_name", "(unnamed)"),
        "tier": cls.get("tier", ""),
        "tier_label": cls.get("tier_label", ""),
        "security_risks": len(security.get("risks", [])),
        "created_at": data.get("created_at", ""),
    }


def list_all():
    """All assessments as short summaries, newest first."""
    return [summarise(data) for data in load_all()]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
