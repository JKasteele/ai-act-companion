"""JSON file persistence for assessments.

One file per assessment in the `data/` directory. Deliberately simple and
inspectable; suitable for synthetic example data.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


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
    """Save an assessment dict. Requires an 'id' field."""
    _ensure_dir()
    path = DATA_DIR / f"{assessment['id']}.json"
    path.write_text(json.dumps(assessment, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


def load(assessment_id):
    path = DATA_DIR / f"{assessment_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_all():
    """All assessments as short summaries, newest first."""
    _ensure_dir()
    items = []
    for path in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        cls = data.get("classification", {})
        items.append({
            "id": data.get("id", path.stem),
            "sys_name": data.get("answers", {}).get("sys_name", "(unnamed)"),
            "tier": cls.get("tier", ""),
            "tier_label": cls.get("tier_label", ""),
            "created_at": data.get("created_at", ""),
        })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
