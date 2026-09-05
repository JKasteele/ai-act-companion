import {
  INVENTORY_KEY,
  newSystem,
  updateAnswers,
  log,
  importSystem,
  restoreInventory,
  requiredMissing,
  routeIntent,
  csvRegister,
} from "./hub-model.mjs";
import { escapeHTML as esc, markdownHTML } from "./markdown.mjs";
import { browserEngine } from "./engine-client.mjs";
import {
  cleanReview,
  startCase,
  acceptProposal,
  saveAction,
  reviewPack,
} from "./casework-model.mjs";
import {
  scenarioCards,
  scenarioBrief,
  caseContext,
  proposalsView,
  dossierFindings,
  actionsView,
} from "./casework.mjs";
const $ = (s) => document.querySelector(s);
let catalogue,
  backend = false,
  publicDemo = false,
  systems = [],
  serverSystems = [],
  selected = null,
  section = 0,
  busy = false,
  currentDocument = null,
  storageOK = true,
  draftDescription = "",
  toastTimer;
try {
  systems = restoreInventory(JSON.parse(localStorage.getItem(INVENTORY_KEY)));
} catch {
  storageOK = false;
}
const all = () => [
  ...systems,
  ...serverSystems,
  ...(catalogue?.examples || []).map((e) => ({
    id: "example-" + e.id,
    exampleId: e.id,
    answers: e.answers,
    result: e.result,
    evidence: [],
    activity: [],
    source: "example",
  })),
];
const editable = () => selected && !selected.source;
function persist() {
  try {
    localStorage.setItem(
      INVENTORY_KEY,
      JSON.stringify({ version: 1, systems }),
    );
    storageOK = true;
  } catch {
    storageOK = false;
  }
  $("#connection-status").textContent = storageOK
    ? "Drafts saved on this device"
    : "Session only · export to keep";
  $("#system-count").textContent = systems.length + serverSystems.length;
}
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("#toast").hidden = true), 4500);
}
function message(text, actions = [], live = false) {
  const box = document.createElement("div");
  box.className = "agent-message";
  box.innerHTML = `<span class="message-label">Companion · ${live ? "live AI draft" : "workflow guidance"}</span>${text
    .split("\n\n")
    .map((p) => `<p>${esc(p)}</p>`)
    .join(
      "",
    )}${actions.map((a) => `<button class="suggestion" data-action="${esc(a.action)}">${esc(a.label)} ↗</button>`).join("")}`;
  $("#messages").append(box);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}
function heading(title, description, action = "") {
  return `<div class="page-heading"><div><p class="context">${selected ? esc(selected.source === "example" ? "Reference example" : "System workspace") : "My workspace"}</p><h1>${esc(title)}</h1><p class="subheading">${esc(description)}</p></div>${action}</div>`;
}
function download(text, name, type = "text/markdown") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function navigate(view, id = selected?.id) {
  const hash =
    id && !["systems", "examples", "new", "about"].includes(view)
      ? `system/${encodeURIComponent(id)}/${view}`
      : view;
  if (location.hash.slice(1) === hash) render();
  else location.hash = hash;
}
function card(s) {
  const a = s.answers;
  return `<a class="system-card" href="#system/${encodeURIComponent(s.id)}/overview"><div class="source-meta"><span>${s.source === "example" ? "Example system" : s.source === "server" ? "Saved in local app" : "Your system"}</span><span class="status-pill ${s.result?.classification ? "blue" : "green"}">${esc(s.result?.classification?.tier_label || "Draft")}</span></div><h3>${esc(a.sys_name)}</h3><p>${esc(a.intended_purpose || a.sys_description || "Complete the system profile to start the assessment.")}</p><div class="card-meta"><span>${esc(a.sys_owner || "Owner not assigned")}</span><span>Open workspace ↗</span></div></a>`;
}
function home() {
  const own = [...systems, ...serverSystems];
  return (
    heading(
      "Your AI systems",
      "Pick up an assessment, investigate a risk, or prepare your next document.",
      '<a class="button primary" href="#new">Add system</a>',
    ) +
    `<section class="start-panel"><span class="companion-mark" aria-hidden="true">✳</span><h2>What would you like to work on?</h2><p>Start with a system. Companion keeps the assessment, evidence, and documentation connected.</p><div class="toolbar"><a class="button primary" href="#new">Assess a new system</a><a class="button secondary" href="#examples">Explore examples</a><a class="text-link" href="#documents">Browse all ${catalogue.reports.length} documents</a></div></section><section class="system-section"><div class="section-heading"><h2>Your assessments <span class="muted">${own.length}</span></h2><div><button class="text-link" data-action="import">Import JSON</button> <button class="text-link" data-action="register">Export register</button></div></div>${own.length ? `<div class="system-grid">${own.map(card).join("")}</div>` : '<div class="empty-state">Your workspace is ready. Add a system or copy an example to begin. Your drafts stay on this device.</div>'}</section><section class="case-invitation"><div><h2>A guided introduction</h2><p>Investigate a health insurer’s conflicting evidence.</p></div><a class="button secondary" href="./case.html">Open case study ↗</a></section>`
  );
}
function exampleView() {
  return (
    heading(
      "Example systems",
      "Explore the complete toolkit across health insurance, recruitment, infrastructure, and general-purpose AI.",
    ) +
    `<h2>Realistic review dossiers</h2><p class="status-line">Fictional organisations. Inspect their documents, review proposed answers, and work through the open decisions.</p>${scenarioCards(catalogue.scenarios || [])}<details class="reference-library" open><summary>Reference profile library · 9 systems</summary><p class="status-line">These are shipped reference profiles. Copy one to your workspace to edit it.</p><div class="system-grid">${all()
      .filter((s) => s.source === "example")
      .map(card)
      .join("")}</div></details>`
  );
}
function tabs(view) {
  return `<nav class="detail-tabs" aria-label="System sections">${[
    ["overview", "Overview"],
    ["intake", "Assessment"],
    ["proposals", "Intake proposals"],
    ["evidence", "Evidence"],
    ["findings", "Findings"],
    ["actions", "Actions"],
    ["documents", "Documents"],
    ["activity", "Activity"],
  ]
    .map(
      ([v, l]) =>
        `<a class="${view === v ? "active" : ""}" href="#system/${encodeURIComponent(selected.id)}/${v}"${view === v ? ' aria-current="page"' : ""}>${l}</a>`,
    )
    .join("")}</nav>`;
}
function profile() {
  const a = selected.answers,
    r = selected.result;
  return (
    caseContext(selected, catalogue.scenarios || []) +
    `<div class="profile-grid">${[
      ["Purpose", a.intended_purpose],
      ["Accountable owner", a.sys_owner],
      ["Role", a.provider_role],
      ["Lifecycle", a.lifecycle_stage],
    ]
      .map(
        ([k, v]) =>
          `<div><dt>${k}</dt><dd>${esc(v || "Not recorded")}</dd></div>`,
      )
      .join(
        "",
      )}</div><section class="detail-block"><h2>System description</h2><p>${esc(a.sys_description || "Add a description in Assessment.")}</p></section>${r?.classification ? `<section class="result-panel"><span class="status-pill blue">${esc(r.classification.tier_label)}</span><h2>Current assessment</h2><p>${esc(r.classification.summary)}</p><p class="status-line">${esc(r.provenance || "Existing saved assessment")} · ${esc(r.knowledge_version || "Recorded engine result")}</p><div class="toolbar"><button class="button primary" data-action="documents">Prepare documents</button><button class="button secondary" data-action="findings">Investigate findings</button></div></section>` : `<section class="review-box"><h2>${r?.status === "incomplete" ? "Screening needs clarification" : "Ready to describe this system?"}</h2><p>${requiredMissing(a, catalogue).length} baseline screening answers remain unknown. Complete the structured assessment before a risk tier is produced.</p><button class="button primary" data-action="intake">Continue assessment</button></section>`}<div class="toolbar"><button class="button secondary" data-action="export-system">Export system JSON</button>${editable() ? '<button class="text-link remove-button" data-action="delete">Remove draft</button>' : '<button class="button primary" data-action="copy">Copy to your workspace</button>'}</div>`
  );
}
function field(q) {
  const a = selected.answers,
    v = a[q.id],
    id = "q-" + q.id;
  let input = "";
  if (q.type === "boolean")
    input = `<select id="${id}" data-field="${q.id}"><option value="">Unknown / not answered</option><option value="true"${v === true ? " selected" : ""}>Yes</option><option value="false"${v === false ? " selected" : ""}>No</option></select>`;
  else if (["select", "radio"].includes(q.type))
    input = `<select id="${id}" data-field="${q.id}"><option value="">Choose / not answered</option>${q.options.map((o) => `<option value="${esc(o.value)}"${v === o.value ? " selected" : ""}>${esc(o.label)}</option>`).join("")}</select>`;
  else if (q.type === "multiselect")
    input = `<div class="multi-options" role="group" aria-labelledby="${id}-label">${q.options.map((o) => `<label><input type="checkbox" data-multi="${q.id}" value="${esc(o.value)}"${Array.isArray(v) && v.includes(o.value) ? " checked" : ""}>${esc(o.label)}</label>`).join("")}</div>`;
  else if (q.type === "table") input = table(q, Array.isArray(v) ? v : []);
  else if (q.type === "textarea")
    input = `<textarea id="${id}" data-field="${q.id}" maxlength="10000" placeholder="${esc(q.placeholder || "")}">${esc(v || "")}</textarea>`;
  else
    input = `<input id="${id}" data-field="${q.id}" maxlength="${q.id === "sys_name" ? 200 : 10000}" value="${esc(v || "")}" placeholder="${esc(q.placeholder || "")}">`;
  return `<div class="field"><label id="${id}-label" ${!["multiselect", "table"].includes(q.type) ? `for="${id}"` : ""}>${esc(q.label)}${q.required ? " *" : ""}</label>${input}${q.help ? `<small>${esc(q.help)}</small>` : ""}</div>`;
}
function table(q, rows) {
  return `<div class="table-editor"><table><thead><tr>${q.columns.map((c) => `<th>${esc(c.label)}</th>`).join("")}<th>Remove</th></tr></thead><tbody>${rows.map((row, i) => `<tr>${q.columns.map((c) => `<td>${c.type === "select" ? `<select data-table="${q.id}" data-row="${i}" data-column="${c.id}" aria-label="${esc(c.label)}"><option value="">Unknown</option>${c.options.map((o) => `<option value="${esc(o.value)}"${row[c.id] === o.value ? " selected" : ""}>${esc(o.label)}</option>`).join("")}</select>` : `<input data-table="${q.id}" data-row="${i}" data-column="${c.id}" aria-label="${esc(c.label)}" maxlength="10000" value="${esc(row[c.id] || "")}">`}</td>`).join("")}<td><button class="icon-button" data-remove-row="${q.id}" data-row="${i}" aria-label="Remove row ${i + 1}">×</button></td></tr>`).join("")}</tbody></table><button class="text-link" data-add-row="${q.id}">Add row</button></div>`;
}
function intake() {
  if (!editable())
    return `<div class="notice">This reference profile is read-only. Copy it to make changes; the copy starts as a draft with unanswered screening questions kept explicit.</div><button class="button primary" data-action="copy">Copy to your workspace</button><details class="trace-detail"><summary>Inspect all existing answers</summary><pre>${esc(JSON.stringify(selected.answers, null, 2))}</pre></details>`;
  const sections = catalogue.questionnaire.sections;
  section = Math.min(section, sections.length - 1);
  const s = sections[section];
  return `${
    selected.result?.missing
      ? `<div class="field-errors">${selected.result.missing.length} screening answers need attention.<ul class="screening-list">${selected.result.missing
          .slice(0, 5)
          .map((m) => `<li>${esc(m.label)}</li>`)
          .join("")}</ul></div>`
      : ""
  }<div class="intake-layout"><nav class="section-nav" aria-label="Assessment sections">${sections.map((s, i) => `<button data-section="${i}" class="${section === i ? "active" : ""}">${esc(s.title.replace(/^\d+\. /, ""))}<span>${s.questions.filter((q) => selected.answers[q.id] !== undefined && selected.answers[q.id] !== "" && selected.answers[q.id] !== null).length}/${s.questions.length} recorded</span></button>`).join("")}</nav><div class="intake-content"><h2>${esc(s.title)}</h2><p>${esc(s.description || "")}</p><div class="field-stack">${s.questions.map(field).join("")}</div><div class="intake-controls"><button class="button secondary" data-action="save-intake">Save answers</button><button class="button secondary" data-action="next-section">Next section</button><button class="button primary" data-action="assess">Review & classify</button></div><p class="status-line">All ${sections.length} sections are available. Unknown answers never default to No. Classification requires complete screening.</p></div></div>`;
}
function collect() {
  if (!editable()) return;
  const answers = structuredClone(selected.answers);
  for (const input of document.querySelectorAll("[data-field]")) {
    const q = catalogue.questionnaire.sections
      .flatMap((s) => s.questions)
      .find((q) => q.id === input.dataset.field);
    if (input.value === "") delete answers[q.id];
    else
      answers[q.id] =
        q.type === "boolean" ? input.value === "true" : input.value;
  }
  const groups = new Set(
    [...document.querySelectorAll("[data-multi]")].map((i) => i.dataset.multi),
  );
  for (const id of groups) {
    const values = [
      ...document.querySelectorAll(`[data-multi="${id}"]:checked`),
    ].map((i) => i.value);
    if (values.length) answers[id] = values;
    else delete answers[id];
  }
  for (const input of document.querySelectorAll("[data-table]")) {
    answers[input.dataset.table] ||= [];
    answers[input.dataset.table][Number(input.dataset.row)] ||= {};
    answers[input.dataset.table][Number(input.dataset.row)][
      input.dataset.column
    ] = input.value;
  }
  if (JSON.stringify(answers) !== JSON.stringify(selected.answers))
    updateAnswers(selected, answers);
  persist();
}
function evidence() {
  return `<section class="detail-block"><h2>Evidence for this system</h2><p>Read the source passages and record additional evidence. Source notes are not verified controls.</p>${editable() ? '<div class="toolbar"><button class="button secondary" data-action="upload-evidence">Import text / Markdown document</button><button class="button secondary" data-action="proposals">Review intake proposals</button></div>' : ""}</section>${selected.evidence?.length ? selected.evidence.map((e, i) => `<article class="evidence-entry" id="evidence-${i}" tabindex="-1"><h3>${esc(e.title)}</h3><blockquote>${esc(e.text)}</blockquote><small>Source ${i + 1} · ${esc(e.reference || "Reviewer-provided note")}</small></article>`).join("") : '<div class="empty-state">Attach a document or note, or start a realistic case from Example systems.</div>'}${editable() ? `<form id="evidence-form" class="review-box evidence-form"><div class="field"><label for="e-title">Source title</label><input id="e-title" required maxlength="200"></div><div class="field"><label for="e-reference">Source reference (optional)</label><input id="e-reference" maxlength="300"></div><div class="field"><label for="e-text">Relevant passage or evidence note</label><textarea id="e-text" required maxlength="10000"></textarea></div><button class="button primary">Attach evidence</button></form>` : '<p class="status-line">Copy this system to attach your own evidence.</p>'}`;
}
function findings() {
  const r = selected.result;
  if (!r?.classification)
    return (
      dossierFindings(selected) +
      '<div class="empty-state">Complete and run the assessment for the separate rule-engine findings. No risk tier is inferred from an incomplete profile.</div><div class="toolbar"><button class="button primary" data-action="intake">Continue assessment</button></div>'
    );
  return `<h2>Classification findings</h2>${(r.classification.findings || []).map((f) => `<article class="finding-detail"><h3>${esc(f.title)}</h3><p>${esc(f.rationale)}</p><small>${esc((f.refs || []).join(", "))}</small></article>`).join("") || '<p class="status-line">No determining finding beyond the recorded classification.</p>'}<section class="detail-block"><h2>AI security</h2><p>Architecture-aware findings from the existing security engine.</p>${(r.security?.risks || []).map((f) => `<article class="finding-detail"><span class="status-pill amber">${esc(f.severity || "Review")}</span><h3>${esc(f.title || f.name || f.id)}</h3><p>${esc(f.rationale || f.description || f.summary || "")}</p></article>`).join("") || '<p class="status-line">No security risks returned for the recorded inputs.</p>'}</section><div class="toolbar"><button class="button secondary" data-report="security">Full security assessment</button><button class="button secondary" data-report="redteam">Red-team plan</button><button class="button secondary" data-report="controls">Control catalogue</button></div><details class="trace-detail"><summary>Inspect the complete result</summary><pre>${esc(JSON.stringify(r, null, 2))}</pre></details>`;
}
const reportDescriptions = {
  risk: "Risk tier, reasoning, and cited rules",
  dpia: "Privacy impact assessment starting point",
  security: "OWASP and architecture-aware security",
  redteam: "Prioritised tests and verification criteria",
  controls: "Defensive controls linked to tests",
  governance: "Owners, review cadence, and exceptions",
  datagov: "Datasets, stewardship, and data quality",
  forensics: "Evidence capture and incident readiness",
};
function documents() {
  return `${!selected ? heading("The complete document toolkit", `All ${catalogue.reports.length} document types from the existing engine, organised around your selected system.`) : '<p class="status-line">Generate a document from this system’s current assessment inputs. All outputs remain drafts for review.</p>'}<label class="status-line" for="report-system">System</label><select id="report-system" class="system-picker"><option value="">Choose a system</option>${all()
    .map(
      (s) =>
        `<option value="${esc(s.id)}"${selected?.id === s.id ? " selected" : ""}>${esc(s.answers.sys_name)}${s.source === "example" ? " (example)" : ""}</option>`,
    )
    .join(
      "",
    )}</select><div class="toolbar"><label for="report-language">Language</label><select id="report-language"><option value="en">English</option><option value="nl">Dutch summary</option></select></div><div class="report-grid">${catalogue.reports.map((r) => `<button class="report-tile" data-report="${r.id}"><strong>${esc(r.label)}</strong><small>${esc(reportDescriptions[r.id] || "Generate, review, and export a draft")}</small></button>`).join("")}</div>`;
}
function activity() {
  return selected.activity?.length
    ? selected.activity
        .slice()
        .reverse()
        .map(
          (e) =>
            `<div class="event">${esc(e.label)}<small>${esc(e.at)}</small></div>`,
        )
        .join("")
    : '<div class="empty-state">No changes have been recorded for this system.</div>';
}
function newView() {
  return (
    heading(
      "Start with your system",
      "Give it a name and describe what it does. You can complete the assessment in sections.",
    ) +
    `<form id="new-form" class="review-box field-stack"><div class="field"><label for="new-name">System name</label><input id="new-name" maxlength="200" required placeholder="e.g. Member support assistant"></div><div class="field"><label for="new-description">What does it do?</label><textarea id="new-description" required maxlength="10000" placeholder="Describe its purpose, users, data, and decisions…">${esc(draftDescription)}</textarea></div><div class="field"><label for="new-owner">Accountable owner (optional)</label><input id="new-owner" maxlength="200" placeholder="Team or role"></div><button class="button primary">Create draft & continue</button><small>Use a synthetic or generic description. No risk tier is assigned until screening is complete.</small></form><div class="toolbar"><button class="text-link" data-action="import">Import existing assessment JSON</button><a class="text-link" href="#examples">Start from an example instead</a></div>`
  );
}
function about() {
  return heading(
    "AI governance, grounded in the work",
    "Describe a system. Investigate its evidence. Prepare a review you can explain.",
  ) + `<article class="about-page">
    <p class="about-intro">AI Act Companion connects structured assessments, security findings and source documents in one workspace. Built by Jesse van de Kasteele as a portfolio project exploring practical, accountable AI assistance.</p>
    <div class="toolbar"><a class="button primary" href="#examples">Explore the cases</a><a class="button secondary" href="https://jessekasteele-ai-act-companion.hf.space/" target="_blank" rel="noreferrer">Open live demo ↗</a><a class="text-link" href="https://github.com/JKasteele/ai-act-companion" target="_blank" rel="noreferrer">View source ↗</a></div>
    <figure class="about-photo"><img src="./assets/about-context.png" alt="Illustrated scenes of member support, water infrastructure and a recruitment conversation" width="2172" height="724"><figcaption>Three fictional settings, realistic review questions. AI-generated editorial illustration.</figcaption></figure>
    <section class="about-section"><h2>Start with a realistic decision</h2><div class="about-sectors"><div><h3>Healthcare</h3><p>A member assistant, sensitive claim details and conflicting evidence about where data goes.</p></div><div><h3>Water operations</h3><p>An operations copilot, critical infrastructure and the boundary between advice and control.</p></div><div><h3>Recruitment</h3><p>A shortlisting workflow, consequential decisions and the evidence needed for meaningful oversight.</p></div></div><p>Each dossier includes source documents, proposed intake answers, findings and follow-up actions. <a class="text-link" href="#examples">Open a dossier</a> or <a class="text-link" href="./case.html">follow the guided insurer case</a>.</p></section>
    <section class="about-section about-work"><h2>From a question to a review pack</h2><ol><li><strong>Describe the system.</strong> Work through 13 intake sections, keeping unanswered questions explicit.</li><li><strong>Investigate the evidence.</strong> Compare source passages, inspect classification and security findings, and record what needs clarification.</li><li><strong>Prepare the next decision.</strong> Assign follow-up actions and generate any of the ${catalogue.reports.length} draft reports for human review.</li></ol></section>
    <section class="about-section"><h2>What the AI does</h2><p>Companion guides you to the relevant tools without requiring a model. When live AI is configured, it can read selected evidence and propose intake answers with source quotations. You review and accept each proposal.</p><p>The Python rule engine computes the risk tier. A model cannot change it, close a finding or approve launch. The guided case and authored dossier proposals are labelled separately from live AI.</p></section>
    <section class="about-section"><h2>Your work and your data</h2><p>Your workspace drafts and notes stay in this browser. Export JSON or a review pack to keep a portable copy. ${backend ? "Assessment and report requests are processed by the Python server. Live AI requests send the selected information to the configured provider." : "Assessment and report generation run on this device using the bundled Python engine; the first operation loads the runtime. This preview does not call a hosted model."}</p><p>The public demo is a shared sandbox: use synthetic data only. Its server lists shipped examples and does not add visitor assessments to a shared inventory.</p></section>
    <details class="about-details"><summary>Full toolkit, integrations and review boundaries</summary><p>Nine reference profiles, all 13 intake sections and all ${catalogue.reports.length} reports remain available. The CLI and MCP server are included in the <a class="text-link" href="https://github.com/JKasteele/ai-act-companion" target="_blank" rel="noreferrer">repository</a>. The original web toolkit is ${backend ? '<a class="text-link" href="/classic">available here</a>' : 'available at /classic in a local Python installation'}.</p><p>All reports are drafts. Reference profiles retain their supplied inputs and are labelled as snapshots; edited copies require complete screening. Evidence notes are reviewer statements, not verified controls. This is a self-assessment aid, not legal advice or certification.</p></details>
  </article>`;
}
function render() {
  if (!catalogue) return;
  const parts = location.hash.slice(1).split("/");
  let view = parts[0] || "systems";
  selected = null;
  if (view === "case") {
    const c = (catalogue.scenarios || []).find((c) => c.id === parts[1]);
    $("#main").innerHTML = c
      ? scenarioBrief(c)
      : heading("Case not found", "Open Example systems to choose a dossier.");
    $("#crumb").textContent = c?.organisation || "Example systems";
    return;
  }
  if (view === "system") {
    selected = all().find((s) => s.id === (parts[1] || ""));
    view = parts[2] || "overview";
  }
  if (parts[0] === "system" && !selected) {
    $("#main").innerHTML =
      heading(
        "System not found",
        "This draft may have been removed or belongs to another browser.",
      ) + '<a href="#systems" class="button primary">Your systems</a>';
    return;
  }
  const renderers = {
    systems: home,
    examples: exampleView,
    new: newView,
    about,
    overview: profile,
    intake,
    proposals: () =>
      editable()
        ? proposalsView(selected, catalogue, !$("#live-mode").disabled)
        : '<p class="notice">Copy this reference profile to review proposals.</p>',
    actions: () =>
      editable()
        ? actionsView(selected)
        : '<p class="notice">Copy this reference profile to track review actions.</p>',
    evidence,
    findings,
    documents,
    activity,
  };
  if (
    !selected &&
    [
      "overview",
      "intake",
      "evidence",
      "findings",
      "activity",
      "proposals",
      "actions",
    ].includes(view)
  )
    view = "systems";
  const fn = renderers[view] || home;
  $("#main").innerHTML =
    (selected
      ? heading(
          selected.answers.sys_name,
          selected.source === "example"
            ? "Reference profile · copy to edit and reassess."
            : "Assess, investigate, and document this system.",
          selected.source
            ? '<button class="button primary" data-action="copy">Copy to workspace</button>'
            : "",
        ) + tabs(view)
      : "") + fn();
  if (view === "findings" && selected?.result?.classification)
    $("#main").insertAdjacentHTML("beforeend", dossierFindings(selected));
  if (view === "documents" && editable())
    $("#main").insertAdjacentHTML(
      "afterbegin",
      '<div class="toolbar"><button class="button primary" data-action="review-pack">Prepare review pack</button><span class="status-line">Includes evidence, actions and review notes; adds recommended engine reports after classification.</span></div>',
    );
  if (view === "evidence" && /^\d+$/.test(parts[3] || ""))
    requestAnimationFrame(() => {
      const node = $(`#evidence-${Number(parts[3])}`);
      node?.scrollIntoView({ block: "center" });
      node?.focus({ preventScroll: true });
    });
  $("#crumb").textContent = selected
    ? selected.answers.sys_name
    : {
        systems: "Your systems",
        examples: "Example systems",
        new: "New assessment",
        documents: "Document toolkit",
        about: "About & integrations",
      }[view] || "Your systems";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const active =
      a.dataset.nav === view || (selected && a.dataset.nav === "systems");
    a.classList.toggle("active", !!active);
    a.toggleAttribute("aria-current", !!active);
  });
}
function setBusy(value, label = "") {
  busy = value;
  $("#engine-status").hidden = !value;
  $("#engine-status").textContent = label;
  $("#chat-form button").disabled = value;
}
async function engine(payload) {
  if (backend) {
    const response = await fetch("/api/workspace/toolkit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "The engine request failed.",
      );
    return result;
  }
  return browserEngine(payload);
}
async function runAssessment() {
  collect();
  if (!editable() || busy) return;
  const target = selected,
    snapshot = JSON.stringify(target.answers);
  setBusy(
    true,
    "Running assessment. The first browser run may take a few seconds…",
  );
  toast(
    backend
      ? "Running assessment…"
      : "Loading the Python assessment engine on this device…",
  );
  try {
    const result = await engine({
      operation: "assess",
      answers: target.answers,
    });
    if (JSON.stringify(target.answers) !== snapshot) return;
    target.result = result;
    if (result.status === "incomplete") {
      const first = result.missing[0]?.id;
      section = Math.max(
        0,
        catalogue.questionnaire.sections.findIndex((s) =>
          s.questions.some((q) => q.id === first),
        ),
      );
    }
    log(
      target,
      result.status === "incomplete"
        ? "Screening incomplete; no classification produced."
        : "Ran the deterministic assessment from reviewed inputs.",
    );
    persist();
    navigate(result.status === "incomplete" ? "intake" : "overview", target.id);
    message(
      result.status === "incomplete"
        ? `${result.missing.length} screening answers still need attention. I’ve kept the system unclassified. Continue the assessment to resolve them.`
        : `The engine returned ${result.classification.tier_label}. You can inspect the findings or prepare a document.`,
      [
        {
          action: result.status === "incomplete" ? "intake" : "findings",
          label:
            result.status === "incomplete"
              ? "Continue screening"
              : "Inspect findings",
        },
      ],
    );
  } catch (e) {
    toast(e.message);
  } finally {
    setBusy(false);
  }
}
async function generateReport(type) {
  if (busy) return;
  if (!selected) {
    toast("Choose a system first.");
    $("#report-system")?.focus();
    return;
  }
  const target = selected,
    language = $("#report-language")?.value || "en";
  setBusy(true, "Preparing your document…");
  currentDocument = null;
  $("#document-title").textContent =
    catalogue.reports.find((r) => r.id === type)?.label || "Document";
  $("#document-content").innerHTML =
    '<p class="busy-indicator">Preparing the document with the Python toolkit…</p>';
  $("#document-dialog").showModal();
  try {
    let result;
    if (target.source === "server") {
      const r = await fetch(
        `/api/assessments/${encodeURIComponent(target.serverId)}/report?type=${encodeURIComponent(type)}&lang=${language}`,
      );
      if (!r.ok)
        throw new Error("The saved assessment report could not be loaded.");
      result = await r.json();
    } else
      result = await engine({
        operation: target.exampleId ? "example_report" : "report",
        example_id: target.exampleId,
        answers: target.answers,
        report_type: type,
        language,
      });
    if (result.status === "incomplete") {
      target.result = result;
      persist();
      $("#document-dialog").close();
      navigate("intake", target.id);
      message(
        "This system needs complete screening before the report can contain a classification. Unknown answers have not been treated as No.",
      );
      return;
    }
    currentDocument = { ...result, system: target.answers.sys_name };
    $("#document-content").innerHTML =
      `<p class="notice">Draft for human review · ${esc(target.answers.sys_name)}</p><div class="toolbar"><button class="button primary" data-action="download-report">Download Markdown</button><button class="button secondary" data-action="print-report">Print / PDF</button></div><article class="document-body">${markdownHTML(result.markdown)}</article>`;
    if (!target.source) {
      log(target, `Generated ${type} document draft.`);
      persist();
    }
  } catch (e) {
    $("#document-content").innerHTML =
      `<p class="error-banner">${esc(e.message)}</p><button class="button secondary" data-report="${esc(type)}">Retry</button>`;
  } finally {
    setBusy(false);
  }
}
async function action(name) {
  if (name === "review-pack") return preparePack();
  if (name === "suggest-intake") return suggestIntake();
  if (name === "upload-evidence" && editable()) {
    $("#evidence-file").click();
    return;
  }
  if (["import", "copy", "new"].includes(name) && systems.length >= 100) {
    toast(
      "This workspace holds up to 100 drafts. Export and remove a draft before adding another.",
    );
    return;
  }
  if (name === "import") {
    $("#import-file").click();
    return;
  }
  if (name === "register") {
    download(
      csvRegister([...systems, ...serverSystems]),
      "ai-system-register.csv",
      "text/csv",
    );
    return;
  }
  if (name === "copy" && selected) {
    const copy = newSystem(selected.answers);
    copy.answers.sys_name += " (working copy)";
    systems.push(copy);
    persist();
    navigate("overview", copy.id);
    toast("Copied as a draft. Review screening before reassessing.");
    return;
  }
  if (name === "save-intake") {
    collect();
    toast("Answers saved; changed inputs invalidate the previous result.");
    return;
  }
  if (name === "next-section") {
    collect();
    section = (section + 1) % catalogue.questionnaire.sections.length;
    render();
    return;
  }
  if (name === "assess") return runAssessment();
  if (name === "export-system" && selected) {
    download(
      JSON.stringify(
        {
          version: 1,
          answers: selected.answers,
          evidence: selected.evidence,
          activity: selected.activity,
          review: selected.review,
        },
        null,
        2,
      ),
      "ai-system.json",
      "application/json",
    );
    return;
  }
  if (name === "delete" && editable()) {
    if (
      !confirm(
        "Remove this browser draft and its evidence notes? Export it first if you need a copy.",
      )
    )
      return;
    systems = systems.filter((s) => s.id !== selected.id);
    persist();
    navigate("systems");
    return;
  }
  if (name === "download-report" && currentDocument) {
    download(currentDocument.markdown, currentDocument.filename);
    return;
  }
  if (name === "print-report") {
    window.print();
    return;
  }
  navigate(name);
}
async function preparePack() {
  if (!editable() || busy) return;
  const target = selected,
    snapshot = structuredClone(selected),
    reports = [];
  setBusy(
    true,
    "Preparing the evidence register, review notes and recommended documents…",
  );
  $("#document-title").textContent = "Review pack";
  $("#document-content").innerHTML =
    '<p class="busy-indicator">Preparing a draft from the current system snapshot…</p>';
  $("#document-dialog").showModal();
  try {
    if (snapshot.result?.classification) {
      const types = (catalogue.scenarios || []).find(
        (c) => c.id === snapshot.review?.caseId,
      )?.reports || ["risk", "security", "governance"];
      for (const report_type of types) {
        const report = await engine({
          operation: "report",
          answers: snapshot.answers,
          report_type,
        });
        if (!report.markdown)
          throw new Error(
            "Screening is incomplete. Return to Assessment before attaching engine reports.",
          );
        reports.push(report);
      }
    }
    currentDocument = {
      markdown: reviewPack(snapshot, reports),
      filename: "ai-governance-review-pack.md",
    };
    $("#document-content").innerHTML =
      `<p class="notice">Draft snapshot · ${reports.length} engine reports attached · no approval granted</p><div class="toolbar"><button class="button primary" data-action="download-report">Download review pack</button><button class="button secondary" data-action="print-report">Print / PDF</button></div><article class="document-body">${markdownHTML(currentDocument.markdown)}</article>`;
    log(
      target,
      `Prepared a review pack with ${reports.length} engine reports.`,
    );
    persist();
  } catch (e) {
    $("#document-content").textContent = e.message;
  } finally {
    setBusy(false);
  }
}
async function suggestIntake() {
  if (!editable() || busy) return;
  if ($("#live-mode").disabled) {
    toast(
      "Live intake requires a configured local AI provider. Realistic cases include authored proposals.",
    );
    return;
  }
  const target = selected,
    snapshot = JSON.stringify({
      answers: target.answers,
      evidence: target.evidence,
    });
  setBusy(true, "Companion is reading sources and preparing intake proposals…");
  try {
    const response = await fetch("/api/workspace/system-chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message:
          "Read the relevant sources and propose supported intake answers. Keep conflicts and missing evidence explicit.",
        answers: target.answers,
        evidence: target.evidence,
        intent: "intake",
      }),
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "The intake request failed.",
      );
    if (
      JSON.stringify({ answers: target.answers, evidence: target.evidence }) !==
      snapshot
    )
      throw new Error(
        "The profile or evidence changed during the request. Ask again using the current version.",
      );
    const proposals = (result.proposals || []).map((p) => ({
      ...p,
      provenance: "Live AI proposal",
      status: "pending",
    }));
    target.review = cleanReview({
      ...target.review,
      proposals: [...target.review.proposals, ...proposals],
    });
    log(
      target,
      `Live AI proposed ${proposals.length} answers for human review; none applied.`,
    );
    persist();
    navigate("proposals", target.id);
    message(
      result.answer +
        "\n\n" +
        (result.events || []).map((e) => e.label).join("\n"),
      [],
      true,
    );
  } catch (e) {
    toast(e.message);
  } finally {
    setBusy(false);
  }
}
document.addEventListener("click", async (event) => {
  const start = event.target.closest("[data-start-case]");
  if (start) {
    if (systems.length >= 100) {
      toast("Export and remove a draft before adding another.");
      return;
    }
    const c = (catalogue.scenarios || []).find(
      (c) => c.id === start.dataset.startCase,
    );
    if (!c) return;
    const s = startCase(
      newSystem({
        sys_name: `${c.organisation} — ${c.name}`,
        sys_description: c.brief,
        sys_owner: c.owner,
      }),
      c,
    );
    log(
      s,
      `Started the fictional ${c.organisation} dossier. No intake proposals accepted.`,
    );
    systems.push(s);
    persist();
    navigate("overview", s.id);
    return;
  }
  const accept = event.target.closest("[data-accept-proposal]"),
    reject = event.target.closest("[data-reject-proposal]");
  if ((accept || reject) && editable() && !busy) {
    const target = selected,
      index = Number(
        (accept || reject).dataset[
          accept ? "acceptProposal" : "rejectProposal"
        ],
      );
    try {
      if (accept) {
        const originalAnswers = JSON.stringify(target.answers);
        const candidate = structuredClone(target);
        acceptProposal(candidate, index);
        setBusy(true, "Validating the proposed answer…");
        const checked = await engine({
          operation: "validate",
          answers: candidate.answers,
        });
        if (!(candidate.review.proposals[index].field in checked.answers))
          throw new Error(
            "This proposal does not name an available intake field.",
          );
        // Do not apply a response if another input changed while validation ran.
        if (
          JSON.stringify(target.answers) !== originalAnswers ||
          selected !== target
        )
          throw new Error("System changed. Review the proposal again.");
        updateAnswers(target, checked.answers);
        target.review.proposals[index].status = "accepted";
        log(
          target,
          `Accepted proposal for ${candidate.review.proposals[index].field}; source remains a reviewer statement.`,
        );
      } else {
        target.review.proposals[index].status = "rejected";
        log(target, "Skipped an intake proposal; current answer unchanged.");
      }
      persist();
      render();
    } catch (e) {
      toast(e.message);
    } finally {
      setBusy(false);
    }
  }
});
document.addEventListener("submit", (event) => {
  const form = event.target;
  if (
    !editable() ||
    !form.matches("[data-action-form], #add-action-form, #decision-form")
  )
    return;
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));
  try {
    if (form.matches("[data-action-form]")) {
      saveAction(selected, Number(form.dataset.actionForm), values);
      log(selected, "Updated follow-up action; evidence remains unverified.");
    }
    if (form.id === "add-action-form") {
      if (selected.review.actions.length >= 50)
        throw new Error("A system can contain up to 50 review actions.");
      if (!values.title.trim() || !values.completion.trim())
        throw new Error("Describe the action and required evidence.");
      selected.review.actions.push(
        cleanReview({ actions: [{ ...values, id: crypto.randomUUID() }] })
          .actions[0],
      );
      log(selected, "Added a follow-up action.");
    }
    if (form.id === "decision-form") {
      if (!values.note.trim() || !values.reviewer.trim())
        throw new Error("Add a reviewer and a review note.");
      selected.review.decisions.push({
        ...values,
        at: new Date().toISOString(),
      });
      selected.review = cleanReview(selected.review);
      log(selected, "Recorded a human review note.");
    }
    persist();
    render();
    toast("Review draft saved.");
  } catch (e) {
    toast(e.message);
  }
});
$("#evidence-file").addEventListener("change", async (event) => {
  const target = selected,
    file = event.target.files[0];
  try {
    if (!file || !editable()) return;
    if (file.size > 60000 || !/\.(txt|md)$/i.test(file.name))
      throw new Error("Choose a UTF-8 .txt or .md document up to 60 KB.");
    const content = await file.text();
    if (!content.trim() || content.includes("\u0000"))
      throw new Error("Choose a readable text document.");
    const chunks = content.match(/[\s\S]{1,9000}/g) || [];
    if (target.evidence.length + chunks.length > 30)
      throw new Error(
        "This document would exceed the limit of 30 source passages.",
      );
    target.evidence.push(
      ...chunks.map((text, i) => ({
        title: `${file.name.slice(0, 150)} — passage ${i + 1}`,
        text,
        reference: `Uploaded text document | ${file.name.slice(0, 160)} | passage ${i + 1} | unverified`,
      })),
    );
    log(
      target,
      `Imported ${file.name.slice(0, 100)} as ${chunks.length} source passages.`,
    );
    persist();
    navigate("evidence", target.id);
  } catch (e) {
    toast(e.message);
  } finally {
    event.target.value = "";
  }
});
document.addEventListener("click", (event) => {
  const b = event.target.closest("[data-action]");
  if (b) {
    event.preventDefault();
    action(b.dataset.action);
  }
  const r = event.target.closest("[data-report]");
  if (r) {
    event.preventDefault();
    if ($("#document-dialog").open) $("#document-dialog").close();
    generateReport(r.dataset.report);
  }
  const s = event.target.closest("[data-section]");
  if (s) {
    collect();
    section = Number(s.dataset.section);
    render();
  }
  const add = event.target.closest("[data-add-row]");
  if (add) {
    collect();
    selected.answers[add.dataset.addRow] ||= [];
    selected.answers[add.dataset.addRow].push({});
    selected.result = null;
    persist();
    render();
  }
  const remove = event.target.closest("[data-remove-row]");
  if (remove) {
    collect();
    selected.answers[remove.dataset.removeRow].splice(
      Number(remove.dataset.row),
      1,
    );
    selected.result = null;
    persist();
    render();
  }
});
document.addEventListener("change", (event) => {
  if (event.target.matches("[data-multi]") && event.target.checked) {
    const field = event.target.dataset.multi;
    for (const input of document.querySelectorAll(`[data-multi="${field}"]`)) {
      if (
        input !== event.target &&
        (event.target.value === "none" || input.value === "none")
      )
        input.checked = false;
    }
  }
  if (event.target.matches("[data-field], [data-multi], [data-table]"))
    collect();
  if (event.target.id === "report-system")
    navigate("documents", event.target.value);
});
document.addEventListener("input", (event) => {
  if (event.target.matches("[data-field], [data-table]")) collect();
});
document.addEventListener("submit", (event) => {
  if (event.target.id === "new-form") {
    event.preventDefault();
    if (systems.length >= 100) {
      toast("Export and remove a draft before adding more than 100 systems.");
      return;
    }
    if (!$("#new-name").value.trim() || !$("#new-description").value.trim()) {
      toast("Add a name and description to create a system.");
      return;
    }
    const s = newSystem({
      sys_name: $("#new-name").value.trim(),
      sys_description: $("#new-description").value.trim(),
      sys_owner: $("#new-owner").value.trim(),
    });
    systems.push(s);
    draftDescription = "";
    log(s, "Created a system draft.");
    persist();
    section = 0;
    navigate("intake", s.id);
    message(
      "Your system has its own workspace. Start with its purpose and role, then work through screening. You can return to any section later.",
    );
  }
  if (event.target.id === "evidence-form") {
    event.preventDefault();
    if (selected.evidence.length >= 30) {
      toast("This draft can contain up to 30 evidence notes.");
      return;
    }
    selected.evidence.push({
      title: $("#e-title").value,
      text: $("#e-text").value,
      reference: $("#e-reference").value,
    });
    log(selected, "Attached an evidence note.");
    persist();
    render();
  }
});
$("#import-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  try {
    if (!file) return;
    if (busy || systems.length >= 100) {
      toast(
        "Finish the current operation and keep the workspace under 100 drafts.",
      );
      return;
    }
    if (file.size > 2000000)
      throw new Error("Choose a JSON file smaller than 2 MB.");
    const s = importSystem(JSON.parse(await file.text()));
    setBusy(true, "Checking the imported system profile…");
    s.answers = (
      await engine({ operation: "validate", answers: s.answers })
    ).answers;
    systems.push(s);
    persist();
    navigate("overview", s.id);
    toast("Imported as a draft. Review before classifying.");
  } catch (e) {
    toast(e.message);
  } finally {
    event.target.value = "";
    setBusy(false);
  }
});
$("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("#message").value.trim();
  if (!text || busy) return;
  $("#message").value = "";
  const el = document.createElement("div");
  el.className = "agent-message user";
  el.textContent = text;
  $("#messages").append(el);
  if ($("#live-mode").checked && selected) {
    const systemName = selected.answers.sys_name;
    setBusy(true, "Companion is reading the selected system and evidence…");
    try {
      const r = await fetch("/api/workspace/system-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          answers: selected.answers,
          evidence: selected.evidence || [],
          example_id: selected.exampleId || "",
          assessment_confirmed: !!selected.result?.classification,
        }),
      });
      const body = await r.json();
      if (!r.ok)
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "The live request failed.",
        );
      message(
        `For ${systemName}:\n\n` +
          body.answer +
          "\n\n" +
          (body.events || []).map((e) => "✓ " + e.label).join("\n") +
          "\n\nSources read: " +
          (body.sources || []).join(", "),
        [],
        true,
      );
    } catch (e) {
      message(e.message);
    } finally {
      setBusy(false);
    }
    return;
  }
  const intent = routeIntent(text);
  if (intent.view === "new") {
    draftDescription = text;
    navigate("new");
    message(
      "Create a system draft from this description, then review the structured screening questions.",
    );
  } else if (intent.view === "examples") {
    navigate("examples");
    message(
      "Choose an example to explore its full assessment and document toolkit.",
    );
  } else if (selected) {
    navigate(intent.view);
    message(
      intent.view === "documents"
        ? "The complete document catalogue is ready for this system. Select a report to generate it."
        : intent.view === "findings"
          ? "These findings come from the assessment engine. The security report, red-team plan, and control catalogue provide more detail."
          : "I’ve opened the relevant part of this system’s workspace.",
      intent.report
        ? [{ action: "documents", label: "Choose the document" }]
        : [],
    );
  } else {
    navigate(intent.view === "documents" ? "documents" : "systems");
    message(
      "Choose a system first so the assessment and documents use its actual profile. Workflow guidance is available without a model.",
      [
        { action: "examples", label: "Choose an example" },
        { action: "new", label: "Create your own system" },
      ],
    );
  }
});
$("#live-mode").addEventListener(
  "change",
  () =>
    ($("#agent-mode").textContent = $("#live-mode").checked
      ? "Live AI · selected system · drafts"
      : "Workflow guidance · no live model"),
);
$("#close-document").addEventListener("click", () =>
  $("#document-dialog").close(),
);
window.addEventListener("hashchange", () => {
  render();
  $("#main").focus({ preventScroll: true });
});
async function init() {
  try {
    const config = await fetch("./mode.json").then((r) => r.json());
    if (!config.static) {
      try {
        const r = await fetch("/api/workspace/catalogue");
        if (r.ok) {
          catalogue = await r.json();
          backend = true;
        }
      } catch {}
    }
    if (!catalogue) {
      const r = await fetch("./catalogue.json");
      if (!r.ok)
        throw new Error(
          "The toolkit catalogue is missing. Build the workspace and reload.",
        );
      catalogue = await r.json();
    }
    if (backend) {
      try {
        const [inventory, status, appConfig] = await Promise.all([
          fetch("/api/assessments").then((r) => r.json()),
          fetch("/api/workspace/case").then((r) => r.json()),
          fetch("/api/config").then((r) => r.json()),
        ]);
        publicDemo = appConfig.demo_mode === true;
        $("#public-demo-notice").hidden = !publicDemo;
        $("#live-mode").disabled = !status.live_configured;
        for (const item of inventory.slice(0, 100)) {
          const r = await fetch(
            `/api/assessments/${encodeURIComponent(item.id)}`,
          );
          if (!r.ok) continue;
          const record = await r.json();
          serverSystems.push({
            id: "saved-" + record.id,
            serverId: record.id,
            answers: record.answers,
            result: { ...record, status: "reference" },
            evidence: [],
            activity: [],
            source: "server",
          });
        }
      } catch {
        toast(
          "Existing saved assessments could not be loaded. Browser drafts are still available.",
        );
      }
    }
    $("#engine-label").innerHTML =
      `<span></span> ${backend ? (publicDemo ? "Public demo · Python engine" : "Python server engine") : "Python engine on this device"}`;
    persist();
    render();
  } catch (e) {
    $("#main").innerHTML =
      heading("Workspace could not be opened", e.message) +
      '<button class="button primary" onclick="location.reload()">Reload</button>';
  }
}
init();
