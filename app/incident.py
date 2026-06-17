"""Serious-incident decision helper (EU AI Act Art. 3(49) + Art. 73).

Pure function `assess_incident(answers) -> dict`. A boolean-driven helper: if any
of the four Art. 3(49) limbs is marked, the incident is a reportable serious
incident and the helper returns the binding Art. 73 reporting deadline (the
shortest applicable). It introduces no judgement — it only reflects the limbs the
human marked (section 10); nothing is auto-inferred from the system description.

The deadline follows Art. 73: report without undue delay and in any event no
later than 15 days (general); 2 days for a widespread infringement or a serious
and irreversible disruption of critical infrastructure; 10 days in the event of a
person's death.

Deterministic and AI-free. Reads only the structured `inc_*` fields, so crafted
free-text cannot change the verdict (asserted in the tests).
"""

from .knowledge import eu_ai_act as eu


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def assess_incident(answers):
    """Return the Art. 3(49) limb evaluation and the Art. 73 reporting deadline."""
    answers = answers or {}

    def a(key):
        return _truthy(answers.get(key))

    limbs = []
    for ref, desc, keys in eu.SERIOUS_INCIDENT["limbs"]:
        limbs.append({
            "ref": ref,
            "desc": desc,
            "met": any(a(k) for k in keys),
        })

    death = a("inc_death")
    critical_infra = a("inc_critical_infra")
    widespread = a("inc_widespread")
    reportable = any(limb["met"] for limb in limbs)

    if not reportable:
        deadline = None
        verdict = (
            "Based on the limbs marked, this does **not** currently meet the "
            "Art. 3(49) definition of a serious incident. If you are assessing a "
            "suspected incident, confirm each limb above before concluding."
        )
    else:
        if widespread or critical_infra:
            deadline = "2 days"
        elif death:
            deadline = "10 days"
        else:
            deadline = "15 days"
        verdict = (
            f"**Reportable serious incident.** Report without undue delay, and in "
            f"any event no later than **{deadline}** (Art. 73)."
        )

    return {
        "limbs": limbs,
        "reportable": reportable,
        "deadline": deadline,
        "verdict": verdict,
        "timeline": [list(row) for row in eu.ART_73_TIMELINE],
        "note": eu.ART_73_NOTE,
        "definition": eu.SERIOUS_INCIDENT["summary"],
    }
