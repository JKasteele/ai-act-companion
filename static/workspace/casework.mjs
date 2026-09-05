import { escapeHTML as esc } from "./markdown.mjs";
import { sourceNote, cleanReview } from "./casework-model.mjs";
export function scenarioCards(cases) {
  return `<div class="scenario-list">${cases.map((c) => `<a class="scenario-card" href="#case/${c.id}"><div class="scenario-sector">${esc(c.sector)}<span>${esc(c.stage)}</span></div><h2>${esc(c.organisation)}</h2><h3>${esc(c.name)}</h3><p>${esc(c.brief)}</p><div class="scenario-bottom"><span>${c.documents.length} documents · ${c.findings.length} review findings</span><strong>Read the brief ↗</strong></div></a>`).join("")}</div>`;
}
export function scenarioBrief(c) {
  return `<div class="page-heading"><div><p class="context">Realistic fictional case · ${esc(c.sector)}</p><h1>${esc(c.organisation)}</h1><p class="subheading">${esc(c.name)}</p></div></div><section class="case-brief"><h2>The situation</h2><p>${esc(c.brief)}</p><h2>Your review question</h2><p class="case-question">${esc(c.decision)}</p><dl class="profile-grid"><div><dt>Accountable owner</dt><dd>${esc(c.owner)}</dd></div><div><dt>Review date</dt><dd>${esc(c.date)}</dd></div></dl><button class="button primary" data-start-case="${c.id}">Start a working copy</button><p class="status-line">A new draft with this document pack and authored review material. You choose which intake proposals to accept.</p></section><h2>Inside the evidence pack</h2><div class="dossier-index">${c.documents.map((d) => `<details><summary><strong>${esc(d.title)}</strong><span>${esc(d.owner)} · v${esc(d.version)} · ${esc(d.date)}</span></summary>${d.sections.map((s) => `<section><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p></section>`).join("")}</details>`).join("")}</div><p class="notice">All organisations, documents and observations are fictional. Findings and proposals are authored case material, not discoveries by a model.</p>`;
}
function sourceLinks(system, sources) {
  return sources
    .map((source) => {
      const note = sourceNote(system, source),
        match = /^evidence(\d+):passage$/.exec(source);
      return match && note
        ? `<a class="text-link" href="#system/${system.id}/evidence/${match[1]}">${esc(note.title)}</a>`
        : `<span>${esc(note?.title || "Source unavailable")}</span>`;
    })
    .join("");
}
export function caseContext(system, cases) {
  const c = cases.find((c) => c.id === system.review?.caseId);
  if (!c) return "";
  const pending = system.review.proposals.filter(
    (p) => p.status === "pending",
  ).length;
  return `<section class="case-brief compact"><p class="context">${esc(c.organisation)} · fictional working dossier</p><h2>${esc(c.decision)}</h2><p>${esc(c.brief)}</p><div class="toolbar"><button class="button primary" data-action="${pending ? "proposals" : "actions"}">${pending ? `Review ${pending} intake proposals` : "Continue follow-up actions"}</button><button class="button secondary" data-action="review-pack">Prepare review pack</button></div><small>The original scenario findings remain open; your review notes are recorded separately.</small></section>`;
}
export function proposalsView(system, catalogue, live) {
  const proposals = system.review?.proposals || [],
    questions = catalogue.questionnaire.sections.flatMap((s) => s.questions);
  return `<div class="section-heading"><h2>Review proposed answers</h2>${live ? '<button class="button secondary" data-action="suggest-intake">Ask live AI to read evidence</button>' : ""}</div><p class="status-line">Accept one answer at a time. Acceptance records your judgment, clears the previous assessment, and does not verify the source.</p>${
    proposals.length
      ? proposals
          .map(
            (p, i) =>
              `<article class="proposal-card"><div class="source-meta"><span>${esc(p.provenance)}</span><span class="status-pill">${esc(p.status)}</span></div><h3>${esc(questions.find((q) => q.id === p.field)?.label || p.field)}</h3><p class="proposed-value">Proposed: <strong>${esc(
                displayValue(
                  p.value,
                  questions.find((q) => q.id === p.field),
                ),
              )}</strong></p><p>Current: ${esc(
                displayValue(
                  system.answers[p.field],
                  questions.find((q) => q.id === p.field),
                ),
              )}</p><blockquote>${esc(p.quote)}</blockquote><p>${esc(p.reason)}</p><div class="source-links">${sourceLinks(system, [p.source])}</div>${p.status === "pending" ? `<div class="toolbar"><button class="button primary" data-accept-proposal="${i}">Accept this answer</button><button class="button secondary" data-reject-proposal="${i}">Keep current answer / skip</button></div>` : ""}</article>`,
          )
          .join("")
      : `<div class="empty-state">Attach evidence and use live AI in a configured local app to propose answers. The realistic cases include authored proposals you can review without a model.</div>`
  }`;
}
function displayValue(value, q) {
  if (value === undefined || value === null || value === "")
    return "Unknown / not answered";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value))
    return value
      .map((v) => q?.options?.find((o) => o.value === v)?.label || String(v))
      .join(", ");
  return q?.options?.find((o) => o.value === value)?.label || String(value);
}
export function dossierFindings(system) {
  const findings = system.review?.findings || [];
  if (!findings.length) return "";
  return `<section class="detail-block"><h2>Evidence review findings</h2><p>Authored scenario findings, separate from the rule engine. A task marked ready for review does not close a finding.</p>${findings.map((f) => `<article class="finding-detail"><span class="status-pill amber">${esc(f.priority)} · Open</span><h3>${esc(f.title)}</h3><p>${esc(f.description)}</p><small>${esc(f.basis)} · ${esc(f.provenance)}</small><div class="source-links">${sourceLinks(system, f.sources)}</div></article>`).join("")}<button class="button primary" data-action="actions">Work on follow-up actions</button></section>`;
}
export function actionsView(system) {
  const review = cleanReview(system.review);
  return `<h2>Follow-up actions</h2><p class="status-line">Record the work, accountable roles and evidence needed for a human review. Ready for review is not approval.</p>${review.actions
    .map(
      (a, i) =>
        `<form class="action-card" data-action-form="${i}"><div class="source-meta"><span>${esc(a.priority)} priority</span><span class="status-pill">${esc(a.status.replaceAll("_", " "))}</span></div><h3>${esc(a.title)}</h3><p><strong>Evidence needed:</strong> ${esc(a.completion)}</p><div class="action-fields"><label>Owner<input name="owner" maxlength="200" value="${esc(a.owner)}"></label><label>Due date<input name="due" type="date" value="${esc(a.due)}"></label><label>Status<select name="status">${[
          ["open", "Open"],
          ["in_progress", "In progress"],
          ["ready_for_review", "Ready for evidence review"],
        ]
          .map(
            ([v, l]) =>
              `<option value="${v}"${a.status === v ? " selected" : ""}>${l}</option>`,
          )
          .join(
            "",
          )}</select></label></div><label>Submitted evidence or reference<textarea name="evidence" maxlength="2000" rows="2">${esc(a.evidence)}</textarea></label><button class="button secondary">Save action</button></form>`,
    )
    .join(
      "",
    )}<details class="review-box"><summary>Add an action</summary><form id="add-action-form" class="field-stack"><label>What needs to happen?<input name="title" required maxlength="2000"></label><label>Evidence needed<textarea name="completion" required maxlength="2000"></textarea></label><button class="button secondary">Add action</button></form></details><section class="detail-block"><h2>Human review notes</h2><p>Record your assessment of the evidence, unresolved questions, and next review. This does not change the engine's result.</p>${review.decisions.map((d) => `<article class="review-note"><strong>${esc(d.reviewer)}</strong><small>${esc(d.at)}</small><p>${esc(d.note)}</p></article>`).join("")}<form id="decision-form" class="field-stack review-box"><label>Reviewer / role<input name="reviewer" required maxlength="200"></label><label>Review note<textarea name="note" required maxlength="2000" placeholder="What can you conclude, what remains unknown, and what should happen next?"></textarea></label><button class="button secondary">Record review note</button></form></section><button class="button primary" data-action="review-pack">Prepare review pack</button>`;
}
