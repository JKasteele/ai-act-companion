"use strict";

// --- state -----------------------------------------------------------------
let QUESTIONNAIRE = null;
let CURRENT = null;        // { id, created_at, answers, classification }
let REPORT_TYPE = "risk";
let REPORT_MD = "";
let REPORT_FILENAME = "report.md";
let AI_STATUS = null;       // { enabled, provider, interactive, available, model, ... }
let EXAMPLES = [];          // ready-made example systems

const NARRATIVE_FIELDS = ["sys_description", "intended_purpose", "human_oversight", "data_sources"];

const $ = (sel) => document.querySelector(sel);
const el = (tag, props = {}, ...kids) => {
  const n = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => {
    if (k === "class") n.className = v;
    else if (k === "html") n.innerHTML = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  });
  kids.flat().forEach((c) => n.append(c?.nodeType ? c : document.createTextNode(c ?? "")));
  return n;
};

// Resolve a citation (e.g. "Art. 6(2)", "Annex III(4)") to an AI Act Explorer URL.
const ROMAN = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7, VIII: 8, IX: 9, X: 10, XI: 11 };
function refUrl(ref) {
  if (!ref) return null;
  let m = ref.match(/Art\.?\s*(\d+)/);
  if (m) return `https://artificialintelligenceact.eu/article/${parseInt(m[1], 10)}/`;
  m = ref.match(/Annex\s+([IVX]+)/);
  if (m && ROMAN[m[1]]) return `https://artificialintelligenceact.eu/annex/${ROMAN[m[1]]}/`;
  return null;
}
function refsSpan(refs, cls) {
  const span = el("span", { class: cls });
  (refs || []).forEach((r, i) => {
    if (i) span.append(", ");
    const url = refUrl(r);
    span.append(url
      ? el("a", { href: url, target: "_blank", rel: "noopener" }, r)
      : document.createTextNode(r));
  });
  return span;
}

// --- init ------------------------------------------------------------------
async function init() {
  QUESTIONNAIRE = await (await fetch("/api/questionnaire")).json();
  $("#form-intro").append(
    el("h2", {}, QUESTIONNAIRE.title),
    el("p", { class: "section-desc" }, QUESTIONNAIRE.intro)
  );
  await loadAiStatus();   // before renderForm: determines whether narrative buttons appear
  renderForm();
  await loadSaved();

  $("#btn-assess").addEventListener("click", assess);
  $("#btn-reset").addEventListener("click", () => { renderForm(); });
  $("#example-select").addEventListener("change", onExampleSelected);
  await loadExamples();
  $("#btn-back").addEventListener("click", showIntake);
  $("#btn-download").addEventListener("click", downloadMarkdown);
  $("#btn-print").addEventListener("click", () => window.print());
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => selectReport(t.dataset.type)));

  $("#btn-ai-prefill").addEventListener("click", aiPrefill);
  $("#btn-ai-copy").addEventListener("click", aiCopyPrompt);
  $("#btn-ai-parse").addEventListener("click", aiParse);

  $("#btn-export-csv").addEventListener("click", exportCsv);
  $("#import-file").addEventListener("change", (e) => {
    if (e.target.files[0]) importJson(e.target.files[0]);
    e.target.value = "";
  });
}

// --- AI layer (phase 4) ----------------------------------------------------
async function loadAiStatus() {
  try {
    AI_STATUS = await (await fetch("/api/ai/status")).json();
  } catch { AI_STATUS = { enabled: false }; }
  if (!AI_STATUS || !AI_STATUS.enabled) return;

  const panel = $("#ai-panel");
  panel.classList.remove("hidden");

  let dot = "off", label = AI_STATUS.provider;
  if (AI_STATUS.provider === "ollama") {
    dot = AI_STATUS.available ? "ok" : "warn";
    label = `Ollama · ${AI_STATUS.model}` + (AI_STATUS.available ? "" : " (unreachable)");
  } else if (AI_STATUS.provider === "manual") {
    dot = "ok"; label = "Manual — paste into your own LLM session";
  }
  $("#ai-provider").innerHTML = `<span class="dot ${dot}"></span>${label}`;
}

function aiSpinner(on) {
  $("#ai-spinner").classList.toggle("hidden", !on);
  $("#btn-ai-prefill").disabled = on;
}

// Client-side timeout: a local model can be slow, but the UI must never hang
// indefinitely.
const AI_CLIENT_TIMEOUT_MS = 120000;

async function fetchJsonWithTimeout(url, payload, ms = AI_CLIENT_TIMEOUT_MS) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload), signal: ctrl.signal,
    });
  } finally { clearTimeout(timer); }
}

async function aiPrefill() {
  const description = $("#ai-desc").value.trim();
  if (!description) { toast("Enter a description first."); return; }
  aiSpinner(true);
  $("#ai-result").classList.add("hidden");
  try {
    const res = await fetchJsonWithTimeout("/api/ai/prefill", { description });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showAiNotice(`<strong>AI call failed.</strong> ${err.detail || res.status}. ` +
        `Tip: pick a faster model (OLLAMA_MODEL) or the manual mode.`, [], []);
      return;
    }
    const data = await res.json();
    if (data.mode === "manual") {
      $("#ai-manual-instructions").textContent = data.instructions || "";
      $("#ai-manual-prompt").value = data.prompt || "";
      $("#ai-manual").classList.remove("hidden");
    } else if (data.mode === "auto") {
      applyDraft(data);
    }
  } catch (e) {
    const msg = e.name === "AbortError"
      ? "The model did not respond within the time limit (GPU may be busy). Try a faster model or the manual mode."
      : `Network error: ${e}`;
    showAiNotice(`<strong>AI call aborted.</strong> ${msg}`, [], []);
  } finally {
    aiSpinner(false);
  }
}

function aiCopyPrompt() {
  const ta = $("#ai-manual-prompt");
  navigator.clipboard?.writeText(ta.value).then(
    () => toast("Prompt copied."),
    () => { ta.select(); document.execCommand("copy"); toast("Prompt copied."); }
  );
}

async function aiParse() {
  const text = $("#ai-manual-answer").value.trim();
  if (!text) { toast("Paste the JSON answer first."); return; }
  const res = await fetch("/api/ai/parse", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) { toast("Parsing failed — is it valid JSON?"); return; }
  applyDraft(await res.json());
}

// Apply the draft to the form (NEVER classify/store automatically).
function applyDraft(data) {
  fillFields(data.answers || {});
  const n = Object.keys(data.answers || {}).length;
  showAiNotice(
    `<strong>${data.hitl_notice || "AI draft — review every field."}</strong> ` +
    `${n} field(s) pre-filled.`,
    data.assumptions || [], data.warnings || []);
  $("#form-intro").scrollIntoView({ behavior: "smooth", block: "start" });
}

function showAiNotice(htmlMsg, assumptions, warnings) {
  const box = $("#ai-result");
  let html = `<div class="ai-notice">${htmlMsg}`;
  if (assumptions && assumptions.length) {
    html += `<div style="margin-top:8px"><em>AI assumptions:</em><ul>` +
      assumptions.map((a) => `<li>${escapeHtml(a)}</li>`).join("") + `</ul></div>`;
  }
  if (warnings && warnings.length) {
    html += `<div class="warn" style="margin-top:6px"><em>Ignored/invalid:</em><ul>` +
      warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join("") + `</ul></div>`;
  }
  html += `</div>`;
  box.innerHTML = html;
  box.classList.remove("hidden");
}

async function aiNarrative(field, btn) {
  const answers = collectAnswers();
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = "⏳…";
  try {
    const res = await fetch("/api/ai/narrative", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ field, answers }),
    });
    if (!res.ok) { toast("AI narrative failed."); return; }
    const data = await res.json();
    if (data.mode === "auto" && data.text) {
      const node = document.getElementById(field);
      if (node) node.value = data.text;
      toast("Draft text inserted — review and adjust.");
    }
  } catch { toast("AI narrative failed."); }
  finally { btn.disabled = false; btn.textContent = orig; }
}

// --- render form -----------------------------------------------------------
function renderForm() {
  const form = $("#intake-form");
  form.innerHTML = "";
  for (const section of QUESTIONNAIRE.sections) {
    const fs = el("fieldset", {}, el("legend", {}, section.title));
    if (section.description) fs.append(el("p", { class: "section-desc" }, section.description));
    for (const q of section.questions) fs.append(renderField(q));
    form.append(fs);
  }
}

function renderField(q) {
  const wrap = el("div", { class: "field" });
  const labelText = [q.label, q.required ? el("span", { class: "req" }, " *") : ""];
  wrap.append(el("label", { class: "q", for: q.id }, ...labelText));

  let input;
  if (q.type === "text") {
    input = el("input", { type: "text", id: q.id, name: q.id, placeholder: q.placeholder || "" });
  } else if (q.type === "textarea") {
    input = el("textarea", { id: q.id, name: q.id, placeholder: q.placeholder || "" });
  } else if (q.type === "select") {
    input = el("select", { id: q.id, name: q.id });
    input.append(el("option", { value: "" }, "— kies —"));
    q.options.forEach((o) => input.append(el("option", { value: o.value }, o.label)));
  } else if (q.type === "boolean") {
    input = el("div", { class: "segmented", id: q.id });
    [["true", "Ja"], ["false", "Nee"]].forEach(([val, lab], i) => {
      input.append(el("label", {},
        el("input", { type: "radio", name: q.id, value: val, ...(i === 1 ? { checked: "checked" } : {}) }),
        el("span", {}, lab)));
    });
  } else if (q.type === "radio") {
    input = el("div", { class: "choice", id: q.id });
    q.options.forEach((o) => input.append(el("label", {},
      el("input", { type: "radio", name: q.id, value: o.value }), o.label)));
  } else if (q.type === "multiselect") {
    input = el("div", { class: "choice", id: q.id });
    q.options.forEach((o) => input.append(el("label", {},
      el("input", { type: "checkbox", name: q.id, value: o.value }), o.label)));
  }
  wrap.append(input);
  if (q.help) wrap.append(el("span", { class: "help" }, q.help));

  // Inline AI draft button for narrative fields (auto provider only).
  if (NARRATIVE_FIELDS.includes(q.id) && AI_STATUS && AI_STATUS.enabled &&
      AI_STATUS.available && !AI_STATUS.interactive) {
    wrap.append(el("button", {
      type: "button", class: "ai-field-btn",
      onclick: (e) => aiNarrative(q.id, e.currentTarget),
    }, "✨ AI draft"));
  }
  return wrap;
}

// --- collect answers --------------------------------------------------------
function collectAnswers() {
  const a = {};
  for (const section of QUESTIONNAIRE.sections) {
    for (const q of section.questions) {
      if (q.type === "boolean") {
        const checked = document.querySelector(`input[name="${q.id}"]:checked`);
        a[q.id] = checked ? checked.value === "true" : false;
      } else if (q.type === "radio") {
        const checked = document.querySelector(`input[name="${q.id}"]:checked`);
        if (checked) a[q.id] = checked.value;
      } else if (q.type === "multiselect") {
        const vals = [...document.querySelectorAll(`input[name="${q.id}"]:checked`)].map((c) => c.value);
        if (vals.length) a[q.id] = vals;
      } else {
        const node = document.getElementById(q.id);
        if (node && node.value) a[q.id] = node.value;
      }
    }
  }
  return a;
}

// Fill fields on the CURRENT form (without re-render/reset).
function fillFields(a) {
  for (const [k, v] of Object.entries(a)) {
    if (Array.isArray(v)) {
      // first clear existing selections of this multiselect
      document.querySelectorAll(`input[name="${k}"]`).forEach((c) => (c.checked = false));
      v.forEach((val) => {
        const c = document.querySelector(`input[name="${k}"][value="${val}"]`);
        if (c) c.checked = true;
      });
    } else if (typeof v === "boolean") {
      const c = document.querySelector(`input[name="${k}"][value="${v}"]`);
      if (c) c.checked = true;
    } else {
      const node = document.getElementById(k);
      if (node && (node.tagName === "INPUT" || node.tagName === "TEXTAREA" || node.tagName === "SELECT")) {
        node.value = v;
      }
      const radio = document.querySelector(`input[name="${k}"][value="${v}"]`);
      if (radio) radio.checked = true;
    }
  }
}

function setAnswers(a) {
  renderForm();
  fillFields(a);
}

// --- run assessment ---------------------------------------------------------
async function assess() {
  const answers = collectAnswers();
  if (!answers.sys_name) { toast("Enter at least a system name."); return; }
  const res = await fetch("/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) { toast("Classification failed."); return; }
  const data = await res.json();
  CURRENT = { id: data.id, created_at: data.created_at, answers, classification: data.classification, security: data.security };
  renderClassification();
  await loadSaved();
  await selectReport("risk");
  showResult();
}

function renderClassification() {
  const c = CURRENT.classification;
  const box = $("#result-content");
  box.innerHTML = "";

  box.append(el("span", { class: `tier-badge tier-${c.tier}` }, c.tier_label));
  box.append(el("p", {}, c.tier_description));
  box.append(el("p", {}, c.summary));

  const app = c.applicability;
  if (app && app.date) {
    const basisEl = refUrl(app.basis)
      ? el("a", { href: refUrl(app.basis), target: "_blank", rel: "noopener" }, `(${app.basis})`)
      : document.createTextNode(`(${app.basis})`);
    box.append(el("p", { class: "applies" },
      el("strong", {}, "Applies from: "), `${app.date} — ${app.what} `, basisEl));
  }

  const blocks = [
    ["Determining findings", c.findings, false],
    ["Transparency obligations (Art. 50)", c.transparency_obligations, false],
    ["GPAI obligations (Chapter V)", c.gpai_obligations, true],
  ];
  for (const [title, findings, isGpai] of blocks) {
    if (!findings || !findings.length) continue;
    const blk = el("div", { class: "result-block" }, el("h3", {}, title));
    findings.forEach((f) => {
      blk.append(el("div", { class: "finding" },
        refsSpan(f.refs, "refs" + (isGpai ? " gpai" : "")),
        el("div", {}, el("strong", {}, f.title)),
        el("div", {}, f.rationale)));
    });
    box.append(blk);
  }

  if (c.high_risk_obligations && c.high_risk_obligations.length) {
    const ul = el("ul", { class: "obligations" });
    c.high_risk_obligations.forEach(([ref, desc]) =>
      ul.append(el("li", {}, el("strong", {}, ref + " "), desc)));
    box.append(el("div", { class: "result-block" },
      el("h3", {}, "High-risk obligations"), ul));
  }

  if (c.recommended_artifacts && c.recommended_artifacts.length) {
    const ul = el("ul", { class: "obligations" });
    c.recommended_artifacts.forEach((x) => ul.append(el("li", {}, x)));
    box.append(el("div", { class: "result-block" },
      el("h3", {}, "Recommended documentation"), ul));
  }

  // AI security lens
  const secp = CURRENT.security;
  if (secp && secp.risks && secp.risks.length) {
    const blk = el("div", { class: "result-block" },
      el("h3", {}, "AI security lens — OWASP LLM Top 10 + MITRE ATLAS"));
    blk.append(el("p", { class: "section-desc" }, secp.summary || ""));
    secp.risks.forEach((r) => {
      let atlas = (r.atlas || []).map((t) => `${t.id} (${t.name})`).join(", ") || "—";
      if (r.atlas_note) atlas += ` — ${r.atlas_note}`;
      blk.append(el("div", { class: "finding security" },
        el("span", { class: "refs sec" }, r.id),
        el("div", {}, el("strong", {}, r.name)),
        el("div", {}, r.summary),
        el("div", { class: "sec-meta" },
          el("div", {}, el("em", {}, "Why: "), r.why),
          el("div", {}, el("em", {}, "MITRE ATLAS: "), atlas),
          el("div", {}, el("em", {}, "EU AI Act: "), (r.ai_act_refs || []).join(", ")),
          el("div", {}, el("em", {}, "NIST AI RMF: "), (r.nist_refs || []).join(", ")),
          el("div", {}, el("em", {}, "Mitigation: "), r.mitigation))));
    });
    if (secp.provenance) blk.append(el("p", { class: "section-desc" }, secp.provenance));
    box.append(blk);
  }
}

// --- reports ----------------------------------------------------------------
async function selectReport(type) {
  REPORT_TYPE = type;
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.type === type));
  const res = await fetch(`/api/assessments/${CURRENT.id}/report?type=${type}`);
  if (!res.ok) { toast("Failed to load report."); return; }
  const data = await res.json();
  REPORT_MD = data.markdown;
  REPORT_FILENAME = data.filename;
  const preview = $("#report-preview");
  preview.innerHTML = mdToHtml(REPORT_MD);
  preview.classList.remove("hidden");
}

function downloadMarkdown() {
  const blob = new Blob([REPORT_MD], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = el("a", { href: url, download: REPORT_FILENAME });
  document.body.append(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

// --- saved assessments ------------------------------------------------------
async function loadSaved() {
  const items = await (await fetch("/api/assessments")).json();
  $("#saved-count").textContent = items.length;
  const list = $("#saved-list");
  list.innerHTML = "";
  if (!items.length) {
    list.append(el("p", { class: "section-desc" }, "No saved assessments yet."));
    return;
  }
  const table = el("table", { class: "inv-table" });
  table.append(el("thead", {}, el("tr", {},
    el("th", {}, "System"), el("th", {}, "Risk tier"), el("th", {}, "Security"),
    el("th", {}, "Created"), el("th", {}, "Actions"))));
  const tbody = el("tbody", {});
  items.forEach((it) => {
    const actions = el("td", { class: "inv-actions" });
    actions.append(el("a", { onclick: () => openSaved(it.id) }, "Open"));
    actions.append(el("a", { onclick: () => exportJson(it.id) }, "JSON"));
    const del = el("a", { class: "danger" }, "Delete");
    del.addEventListener("click", () => confirmDelete(del, it.id));
    actions.append(del);
    tbody.append(el("tr", {},
      el("td", {}, it.sys_name || "(unnamed)"),
      el("td", {}, el("span", {
        class: `tier-badge tier-${it.tier}`, style: "font-size:.72rem;padding:2px 9px;",
      }, it.tier_label || it.tier || "—")),
      el("td", {}, String(it.security_risks ?? 0)),
      el("td", { class: "inv-date" },
        (it.created_at || "").replace("T", " ").replace("+00:00", "")),
      actions));
  });
  table.append(tbody);
  list.append(table);
}

function confirmDelete(linkEl, id) {
  if (linkEl.dataset.armed === "1") { deleteAssessment(id); return; }
  linkEl.dataset.armed = "1";
  const orig = linkEl.textContent;
  linkEl.textContent = "Confirm?";
  setTimeout(() => { linkEl.dataset.armed = ""; linkEl.textContent = orig; }, 3000);
}

async function deleteAssessment(id) {
  const res = await fetch(`/api/assessments/${id}`, { method: "DELETE" });
  if (!res.ok) { toast("Delete failed."); return; }
  toast("Deleted.");
  await loadSaved();
}

async function exportJson(id) {
  const data = await (await fetch(`/api/assessments/${id}`)).json();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = el("a", { href: url, download: `${id}.json` });
  document.body.append(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

function exportCsv() {
  const a = el("a", { href: "/api/export.csv", download: "ai-act-inventory.csv" });
  document.body.append(a); a.click(); a.remove();
}

async function importJson(file) {
  try {
    const data = JSON.parse(await file.text());
    setAnswers(data.answers || data);   // accept a full assessment or bare answers
    showIntake();
    toast("Imported — review and classify.");
  } catch { toast("Import failed — invalid JSON."); }
}

async function openSaved(id) {
  const data = await (await fetch(`/api/assessments/${id}`)).json();
  CURRENT = data;
  setAnswers(data.answers || {});
  renderClassification();
  await selectReport("risk");
  showResult();
}

// --- view switches ----------------------------------------------------------
function showResult() {
  $("#intake-section").classList.add("hidden");
  $("#result-section").classList.remove("hidden");
  $("#reports-section").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
function showIntake() {
  $("#intake-section").classList.remove("hidden");
  $("#result-section").classList.add("hidden");
  $("#reports-section").classList.add("hidden");
  $("#report-preview").classList.add("hidden");
}

// --- examples ---------------------------------------------------------------
async function loadExamples() {
  try { EXAMPLES = await (await fetch("/api/examples")).json(); }
  catch { EXAMPLES = []; }
  const sel = $("#example-select");
  EXAMPLES.forEach((ex) => {
    sel.append(el("option", { value: ex.id }, `${ex.name} — ${ex.tier_label}`));
  });
}

function onExampleSelected(e) {
  const ex = EXAMPLES.find((x) => x.id === e.target.value);
  e.target.value = "";   // reset so the same example can be re-picked
  if (!ex) return;
  setAnswers(ex.answers);
  showIntake();
  toast(`Loaded example: ${ex.name}`);
}

function fillExample() {
  setAnswers({
    sys_name: "TalentMatch CV screening",
    sys_version: "1.0",
    sys_owner: "Example Ltd.",
    sys_description: "A machine-learning model that automatically ranks incoming job application CVs by suitability for a vacancy.",
    intended_purpose: "Support recruiters in pre-selecting candidates.",
    provider_role: "provider",
    eu_market: true,
    lifecycle_stage: "production",
    hr_usecases: ["employment"],
    hr_does_profiling: true,
    data_personal: true,
    automated_decision: true,
    data_scale: "medium",
    data_sources: "Internal ATS database with synthetic example CVs.",
    autonomy_level: "advisory",
    can_override: true,
    human_oversight: "A recruiter manually reviews every shortlist suggested by the model before candidates are invited.",
    sec_is_llm: false,
    sec_third_party_models: true,
    sec_external_data: true,
    sec_agentic: false,
    sec_public: false,
    sec_outputs_to_systems: false,
  });
  toast("Example loaded — adjust and classify.");
}

// --- toast -----------------------------------------------------------------
let toastTimer;
function toast(msg) {
  let t = $(".toast");
  if (!t) { t = el("div", { class: "toast" }); document.body.append(t); }
  t.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.remove(), 2600);
}

// --- minimal Markdown -> HTML -----------------------------------------------
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, (_, x) => `<code>${x}</code>`)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/_([^_]+)_/g, "<em>$1</em>");
}
function mdToHtml(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;
  const isTableSep = (l) => /^\s*\|?[\s:|-]+\|?\s*$/.test(l) && l.includes("-");

  while (i < lines.length) {
    let line = lines[i];

    if (/^\s*$/.test(line)) { i++; continue; }

    // Heading
    let m = line.match(/^(#{1,6})\s+(.*)$/);
    if (m) { const lvl = m[1].length; out.push(`<h${lvl}>${inline(escapeHtml(m[2]))}</h${lvl}>`); i++; continue; }

    // Horizontal rule
    if (/^(-{3,}|\*{3,})\s*$/.test(line)) { out.push("<hr/>"); i++; continue; }

    // Table: current line contains '|' and the next is a separator
    if (line.includes("|") && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      const parseRow = (l) => l.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map((c) => c.trim());
      const header = parseRow(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes("|") && !/^\s*$/.test(lines[i])) {
        rows.push(parseRow(lines[i])); i++;
      }
      let t = "<table><thead><tr>" + header.map((h) => `<th>${inline(escapeHtml(h))}</th>`).join("") + "</tr></thead><tbody>";
      rows.forEach((r) => { t += "<tr>" + r.map((c) => `<td>${inline(escapeHtml(c))}</td>`).join("") + "</tr>"; });
      t += "</tbody></table>";
      out.push(t);
      continue;
    }

    // Blockquote
    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) { buf.push(lines[i].replace(/^>\s?/, "")); i++; }
      out.push(`<blockquote>${inline(escapeHtml(buf.join(" ")))}</blockquote>`);
      continue;
    }

    // Unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, "")); i++;
      }
      out.push("<ul>" + items.map((it) => `<li>${inline(escapeHtml(it))}</li>`).join("") + "</ul>");
      continue;
    }

    // Ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, "")); i++;
      }
      out.push("<ol>" + items.map((it) => `<li>${inline(escapeHtml(it))}</li>`).join("") + "</ol>");
      continue;
    }

    // Paragraph
    const buf = [];
    while (i < lines.length && !/^\s*$/.test(lines[i]) &&
           !/^(#{1,6})\s/.test(lines[i]) && !lines[i].includes("|") &&
           !/^\s*[-*]\s+/.test(lines[i]) && !/^>\s?/.test(lines[i])) {
      buf.push(lines[i]); i++;
    }
    out.push(`<p>${inline(escapeHtml(buf.join(" ")))}</p>`);
  }
  return out.join("\n");
}

init();
