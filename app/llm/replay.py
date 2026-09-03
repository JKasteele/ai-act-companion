"""Replay provider: pre-recorded drafts for the public sandbox.

The public demo runs with no model and no egress, which hides the AI-assist
flow (free text -> draft -> human review -> deterministic classification).
This provider *replays* that flow without a model: it matches the visitor's
description against the shipped synthetic examples and returns the closest
example's intake fields as the draft, with the same validation, the same
human-in-the-loop notice and the same "the engine decides the tier" guarantee
as a real model.

It is labelled as a replay everywhere it appears (status, notice, assumptions)
so nobody mistakes it for inference. No network, no randomness: the match is a
deterministic keyword overlap, ties broken by example name.
"""

import json
import re
from pathlib import Path

from .base import LLMProvider

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"

# Only the intake fields a model could plausibly infer from a free-text
# description are replayed (sections 1-9). Governance-record sections (11-13)
# are facts about the organisation, not about the system, so they stay empty
# for the human to fill in — exactly as with a real model.
_REPLAY_PREFIXES = ("sys_", "org_", "intended_", "provider_role", "eu_market", "lifecycle_",
                    "hr_", "p_", "t_", "gpai_", "data_", "automated_", "affects_",
                    "autonomy_", "can_override", "human_oversight", "sec_", "arch_")

_STOP = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "with", "that",
         "this", "is", "are", "it", "its", "by", "as", "at", "be", "we", "our", "system",
         "ai", "model", "uses", "use", "using", "based", "data", "which", "from", "into"}


def _tokens(text):
    return {w for w in re.findall(r"[a-z][a-z0-9\-]{2,}", (text or "").lower()) if w not in _STOP}


def load_library():
    """Shipped examples as (name, keyword set, replayable answers, comment)."""
    lib = []
    for p in sorted(_EXAMPLES_DIR.glob("*.json")):
        if p.name == "golden_set.json":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or "sys_name" not in d:
            continue
        haystack = " ".join(str(d.get(k, "")) for k in
                            ("sys_name", "sys_description", "intended_purpose", "_comment",
                             "data_sources", "human_oversight"))
        answers = {k: v for k, v in d.items() if k.startswith(_REPLAY_PREFIXES)}
        lib.append({"id": p.stem, "name": d.get("sys_name", p.stem), "keywords": _tokens(haystack),
                    "answers": answers, "comment": d.get("_comment", "")})
    return lib


def best_match(description, library=None):
    """Deterministic: highest keyword overlap wins; ties -> alphabetical id."""
    library = library if library is not None else load_library()
    words = _tokens(description)
    scored = sorted(((len(words & item["keywords"]), item["id"], item) for item in library),
                    key=lambda t: (-t[0], t[1]))
    if not scored:
        return None, 0
    score, _id, item = scored[0]
    return item, score


class ReplayProvider(LLMProvider):
    name = "replay"
    interactive = False

    def status(self):
        return {"provider": self.name, "interactive": False, "available": True,
                "replay": True,
                "model": "pre-recorded drafts (sandbox — no live model, no egress)"}

    def generate(self, system, user, as_json=True):
        """Return text shaped like a model response: JSON for prefill, prose for
        narrative. The description / answers are parsed out of the prompt the
        service built, so the service code path is identical to a real model."""
        if as_json:
            m = re.search(r'DESCRIPTION OF THE AI SYSTEM:\n"""\n(.*?)\n"""', user, re.DOTALL)
            description = m.group(1) if m else user
            item, score = best_match(description)
            if item is None or score == 0:
                return json.dumps({"answers": {"sys_description": description.strip()[:2000]},
                                   "assumptions": [
                                       "Replay mode: no shipped example resembles this "
                                       "description, so only the description was carried over. "
                                       "Fill in the form by hand (or run locally with Ollama)."]})
            assumptions = [
                f"Replay mode (sandbox): this draft is the shipped synthetic example "
                f"'{item['name']}', chosen by keyword match ({score} overlapping terms), "
                "not a live model inference.",
                "Governance-record sections (data governance, forensic readiness, "
                "governance register) are left for you to complete, as a model "
                "cannot know them from a description.",
                "Every field is a draft: review it before you classify.",
            ]
            return json.dumps({"answers": item["answers"], "assumptions": assumptions})
        # narrative: a plain, templated paragraph naming what was asked for
        m = re.search(r"^Draft (.+?)\.\n", user)
        what = m.group(1) if m else "the requested section"
        return (f"[Replay draft — sandbox] Here a local model would draft {what} from the "
                "answers you gave, in two to five sentences, for you to review. The public "
                "sandbox runs no model, so this placeholder marks where that draft goes; run "
                "locally with Ollama (LLM_PROVIDER=ollama) to get the real draft.")
