"""Report language support.

The engine and the full reports are English (the language of the regulation's
article tokens and of every standard cited). `--lang nl` prepends a **Dutch
summary block** to any report — risk tier, applicability, determining findings,
transparency duties, recommended documentation and, for the governance lenses,
their headline figures — so a Dutch reviewer, board or supervisor gets the
verdict in their own language while the citable body stays English. The block
is generated from the structured classification, never from free text, and is
labelled as a summary, not a translation.
"""

from ._normalize import truthy
from .knowledge import eu_ai_act as eu

LANGS = ("en", "nl")

TIER_NL = {
    eu.TIER_PROHIBITED: "Verboden (onaanvaardbaar risico)",
    eu.TIER_HIGH: "Hoog risico",
    eu.TIER_LIMITED: "Beperkt risico (transparantieverplichtingen)",
    eu.TIER_MINIMAL: "Minimaal risico",
}

ROLE_NL = {
    "provider": "aanbieder", "deployer": "gebruiksverantwoordelijke",
    "both": "aanbieder én gebruiksverantwoordelijke", "other": "anders / nog onbekend",
}

# Recommended-artifact strings (classifier._recommended_artifacts) -> Dutch.
ARTIFACT_NL = {
    "AI risk assessment report": "AI-risicobeoordeling",
    "AI literacy measures / staff training record (AI Act Art. 4)":
        "AI-geletterdheidsmaatregelen / trainingsregister (AI-verordening art. 4)",
    "DPIA (data protection impact assessment, GDPR Art. 35)":
        "DPIA (gegevensbeschermingseffectbeoordeling, AVG art. 35)",
    "Data governance & quality record (AI Act Art. 10)":
        "Datagovernance- en datakwaliteitsdossier (AI-verordening art. 10)",
    "Data governance & quality record (good practice; GDPR Art. 5(1)(d))":
        "Datagovernance- en datakwaliteitsdossier (goede praktijk; AVG art. 5(1)(d))",
    "Bias/fairness audit report (AI Act Art. 10)":
        "Bias-/fairnessauditrapport (AI-verordening art. 10)",
    "Technical documentation (AI Act Art. 11 + Annex IV)":
        "Technische documentatie (AI-verordening art. 11 + bijlage IV)",
    "Fundamental rights impact assessment - FRIA (AI Act Art. 27)":
        "Grondrechteneffectbeoordeling - FRIA (AI-verordening art. 27)",
    "Bias audit checklist (good practice)": "Bias-auditchecklist (goede praktijk)",
    "AI security assessment (OWASP LLM Top 10 + MITRE ATLAS)":
        "AI-securitybeoordeling (OWASP LLM Top 10 + MITRE ATLAS)",
}

BAND_NL = {
    "Not ready": "Niet gereed", "Partially ready": "Deels gereed",
    "Ready with gaps": "Gereed met hiaten", "Forensic-ready": "Forensisch gereed",
}

STATUS_NL = {
    "Proposed": "Voorgesteld", "Approved": "Goedgekeurd", "In review": "In herbeoordeling",
    "Running under exception": "Loopt onder uitzondering", "Retired": "Uitgefaseerd",
}

DISCLAIMER_NL = (
    "Deze samenvatting is een Nederlandse weergave van de kern van het rapport; "
    "het volledige, citeerbare rapport hieronder is in het Engels. Dit is een "
    "hulpmiddel voor een gestructureerde zelfbeoordeling, geen juridisch advies."
)


def _cell(text):
    """Neutralise free text for a Markdown table cell."""
    return " ".join(str(text or "").split()).replace("|", "\\|") or "-"


def _applies_nl(app):
    date = app.get("date", "-")
    basis = app.get("basis", "")
    what = app.get("what", "")
    if date == "-":
        return "geen verplichte datum (minimaal risico)"
    if "Annex III" in what and "postponed" in what:
        what_nl = ("hoog-risicoverplichtingen voor bijlage III-systemen; door de Digital "
                   "Omnibus (Verordening (EU) 2026/1744) verschoven van 2 aug 2026")
    elif "Annex I" in what:
        what_nl = ("hoog-risicoverplichtingen voor art. 6(1)/bijlage I-systemen "
                   "(gereguleerde producten); verschoven van 2 aug 2027")
    elif "Transparency" in what:
        what_nl = "transparantieverplichtingen (art. 50) gelden (in werking)"
    elif "Prohibition" in what:
        what_nl = "verbod onder art. 5 geldt al"
    elif "GPAI" in what:
        what_nl = "verplichtingen voor AI-modellen voor algemene doeleinden (hoofdstuk V)"
    else:
        what_nl = what
    return f"{date} — {what_nl} ({basis})" if basis else f"{date} — {what_nl}"


def summary_block_nl(assessment):
    """Dutch summary block (Markdown) built from the structured assessment."""
    answers = assessment.get("answers", {}) or {}
    cls = assessment.get("classification", {}) or {}
    tier = cls.get("tier", eu.TIER_MINIMAL)
    role = (answers.get("provider_role") or "").strip().lower()
    md = ["\n## Samenvatting (NL)\n", f"\n> _{DISCLAIMER_NL}_\n\n",
          "| Onderwerp | Waarde |\n|---|---|\n",
          f"| Systeem | {_cell(answers.get('sys_name'))} |\n",
          f"| Rol (art. 3) | {ROLE_NL.get(role, _cell(role))} |\n",
          f"| Risicoklasse | **{TIER_NL.get(tier, tier)}** |\n",
          f"| Van toepassing vanaf | {_cell(_applies_nl(cls.get('applicability') or {}))} |\n"]
    if cls.get("out_of_scope"):
        md.append(f"| Toepassingsgebied | Buiten de werkingssfeer "
                  f"({cls['out_of_scope'].get('ref', 'art. 2')}) |\n")
    findings = cls.get("findings") or []
    if findings:
        md.append("| Bepalende bevindingen | " + "; ".join(
            f"{_cell(f.get('title'))} ({', '.join(f.get('refs', []))})" for f in findings)
            + " |\n")
    trans = cls.get("transparency_obligations") or []
    md.append(f"| Transparantieverplichtingen (art. 50) | "
              f"{'; '.join(_cell(t.get('title')) for t in trans) if trans else 'geen'} |\n")
    gpai = cls.get("gpai_obligations") or []
    if gpai:
        md.append("| GPAI-modelverplichtingen (hoofdstuk V) | ja — "
                  + "; ".join(_cell(g.get('title')) for g in gpai) + " |\n")
    if truthy(answers.get("data_personal")):
        md.append("| Persoonsgegevens | ja — AVG van toepassing"
                  + ("; bijzondere categorieën" if truthy(answers.get("data_special_category"))
                     else "") + " |\n")
    arts = cls.get("recommended_artifacts") or []
    if arts:
        md.append("| Aanbevolen documentatie | "
                  + "; ".join(ARTIFACT_NL.get(a, a) for a in arts) + " |\n")

    # Governance lenses, when their structured results are on the assessment.
    fr = assessment.get("forensics")
    if fr:
        md.append(f"| Forensische gereedheid | {fr.get('total')}/{fr.get('max')} — "
                  f"{BAND_NL.get(fr.get('band'), fr.get('band'))} |\n")
    gov = assessment.get("governance")
    if gov:
        nxt = gov.get("next_review") or "onbekend"
        md.append(f"| Governancestatus | {STATUS_NL.get(gov.get('status_label'), gov.get('status_label'))}"
                  f"; volgende review {nxt}"
                  + (" — **te laat**" if gov.get("review_overdue") else "") + " |\n")
    dgs = assessment.get("datagov")
    if dgs:
        counts = dgs.get("gap_counts", {})
        md.append(f"| Datagovernance | {dgs.get('dataset_count', 0)} dataset(s); "
                  f"hiaten hoog {counts.get('high', 0)}, midden {counts.get('medium', 0)}, "
                  f"laag {counts.get('low', 0)} |\n")
    return "".join(md)


def localise(markdown, assessment, lang="en"):
    """Insert the language block into a rendered report. 'en' returns the input."""
    if lang not in LANGS:
        raise ValueError(f"Unsupported language: {lang}")
    if lang == "en":
        return markdown
    block = summary_block_nl(assessment)
    lines = markdown.split("\n")
    # Insert after the disclaimer blockquote that every report header carries;
    # fall back to right after the H1.
    idx = next((i for i, line in enumerate(lines)
                if line.startswith("> This report was generated")), 0)
    lines.insert(idx + 1, block)
    return "\n".join(lines)
