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
  await loadConfig();
  loadTimeline();   // non-blocking: render the AI Act countdown when it returns
  // A failed fetch here must not abort init(): the listeners below still need
  // to be wired so the UI stays responsive and can surface the error.
  try {
    QUESTIONNAIRE = await (await fetch("/api/questionnaire")).json();
    $("#form-intro").append(
      el("h2", {}, QUESTIONNAIRE.title),
      el("p", { class: "section-desc" }, QUESTIONNAIRE.intro)
    );
  } catch {
    toast("Could not load the questionnaire — is the server reachable?");
  }
  await loadAiStatus();   // before renderForm: determines whether narrative buttons appear
  renderForm();
  await loadSaved();

  $("#btn-assess").addEventListener("click", assess);
  $("#btn-reset").addEventListener("click", () => { renderForm(); });
  $("#example-select").addEventListener("change", onExampleSelected);
  await loadExamples();
  await loadHowto();
  const tourBtn = $("#btn-tour");
  if (tourBtn) tourBtn.addEventListener("click", startTour);
  $("#btn-back").addEventListener("click", showIntake);
  $("#btn-download").addEventListener("click", downloadMarkdown);
  $("#btn-print").addEventListener("click", () => window.print());
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => selectReport(t.dataset.type)));

  $("#btn-ai-prefill").addEventListener("click", aiPrefill);
  $("#btn-ai-copy").addEventListener("click", aiCopyPrompt);
  $("#btn-ai-parse").addEventListener("click", aiParse);

  $("#btn-export-csv").addEventListener("click", exportCsv);
  const langSel = $("#report-lang");
  if (langSel) langSel.addEventListener("change", () => { if (CURRENT) selectReport(REPORT_TYPE); });
  const regBtn = $("#btn-export-register");
  if (regBtn) regBtn.addEventListener("click", exportRegisterCsv);
  $("#import-file").addEventListener("change", (e) => {
    if (e.target.files[0]) importJson(e.target.files[0]);
    e.target.value = "";
  });
}

// --- demo mode (public sandbox banner) -------------------------------------
async function loadConfig() {
  let cfg = {};
  try { cfg = await (await fetch("/api/config")).json(); } catch { cfg = {}; }
  renderReportTabs(cfg.report_types);
  if (cfg.version) {
    const v = $("#app-version");
    if (v) v.textContent = `AI Act Companion v${cfg.version}`;
  }
  if (!cfg.demo_mode) return cfg;
  const main = document.querySelector("main.wrap") || document.body;
  const banner = el("div", { class: "demo-banner no-print" },
    el("strong", {}, "Public sandbox. "),
    "Synthetic / example data only — do not enter real or personal data. " +
    "Assessments are not persisted and are visible to other visitors during " +
    "the demo. The AI assist may run live (Claude, capped budget) or in replay " +
    "mode (pre-recorded drafts) — the label on the AI panel says which; the " +
    "classification is always the real deterministic engine.");
  main.prepend(banner);
  return cfg;
}

// Render the report tabs from the engine's catalogue so the frontend never
// drifts from reports.REPORT_CATALOG. If /api/config is unreachable, fall back
// to the core report so the Documentation section is never left without tabs.
function renderReportTabs(types) {
  const container = document.querySelector(".report-tabs");
  if (!container) return;
  if (!Array.isArray(types) || !types.length) {
    types = [{ type: "risk", label: "Risk assessment" }];
  }
  container.innerHTML = "";
  types.forEach((t, i) => container.append(
    el("button", { type: "button", class: i === 0 ? "tab active" : "tab",
                   "data-type": t.type }, t.label)));
}

// --- EU AI Act countdown (presentational; dates come from the engine) ------
async function loadTimeline() {
  let data;
  try { data = await (await fetch("/api/timeline")).json(); }
  catch { return; }
  const box = document.getElementById("aiact-countdown");
  if (!box || !data || !data.milestones) return;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const next = data.milestones
    .map((m) => ({ ...m, d: new Date(m.date + "T00:00:00") }))
    .filter((m) => m.d >= today)
    .sort((a, b) => a.d - b.d)[0];
  if (!next) return;
  const days = Math.round((next.d - today) / 86400000);
  const dateStr = next.d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  box.innerHTML = "";
  box.append(
    el("span", { class: "cd-num" }, String(days)),
    el("span", { class: "cd-unit" }, days === 1 ? "day" : "days"),
    el("span", { class: "cd-label" }, `until ${next.label}`),
    el("span", { class: "cd-date" }, dateStr),
  );
  if (data.last_reviewed) {
    const amend = (data.amendments || []).map((a) => a.name).join(", ");
    box.append(el("span", { class: "cd-meta" },
      `Knowledge base reviewed ${data.last_reviewed}${amend ? " · incl. " + amend : ""}`));
  }
  box.classList.remove("hidden");
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
  } else if (AI_STATUS.fallback_from === "anthropic" && AI_STATUS.provider === "replay") {
    dot = "replay";
    label = "Sandbox replay — the live-AI budget for this demo is used up (drafts are pre-recorded)";
  } else if (AI_STATUS.provider === "replay") {
    dot = "replay"; label = "Sandbox replay — drafts are pre-recorded (no live model)";
  } else if (AI_STATUS.provider === "anthropic") {
    if (AI_STATUS.available) {
      const b = AI_STATUS.budget || {};
      dot = "ok";
      label = `Live AI · ${AI_STATUS.model} · budget left $${(b.remaining_usd ?? 0).toFixed(2)} · ` +
        `${b.calls_today ?? 0}/${b.daily_cap ?? 0} calls today`;
    } else {
      dot = "warn"; label = "Anthropic provider configured but no API key";
    }
  }
  const provEl = $("#ai-provider");
  provEl.innerHTML = "";
  provEl.append(el("span", { class: `dot ${dot}` }), label);
  if (AI_STATUS.replay) renderReplaySuggestions();
}

// In replay mode, offer a few descriptions that map onto shipped examples so a
// visitor can see the whole flow in three clicks.
const REPLAY_SUGGESTIONS = [
  ["Health-insurance pricing", "We score applicants for a supplementary health insurance package and propose a premium band; an underwriter decides. We are the deployer, the model is licensed from a vendor."],
  ["Claims fraud scoring", "A model scores incoming care-provider claims for anomalies and possible fraud and routes high scores to an investigator before payment."],
  ["Customer-service assistant", "A chat assistant on a hosted large language model answers insured persons' questions about coverage and looks up their own claim status through an API."],
  ["CV screening", "A machine-learning model ranks incoming job applications by suitability for a vacancy to support recruiters in pre-selecting candidates."],
];

function renderReplaySuggestions() {
  const box = $("#ai-suggest");
  if (!box) return;
  box.innerHTML = "";
  box.append(el("span", { class: "ai-suggest-label" }, "Try one:"));
  REPLAY_SUGGESTIONS.forEach(([label, text]) => box.append(el("button", {
    type: "button", class: "chip", onclick: () => { $("#ai-desc").value = text; $("#ai-desc").focus(); },
  }, label)));
  box.classList.remove("hidden");
  const desc = $("#ai-desc");
  if (desc && !desc.value) desc.value = REPLAY_SUGGESTIONS[0][1];
}

// --- how it works: stats, MCP transcript, guided tour ------------------------------
async function loadHowto() {
  const stats = $("#howto-stats");
  if (stats) {
    const reports = (document.querySelectorAll(".report-tabs .tab") || []).length;
    const sections = QUESTIONNAIRE ? QUESTIONNAIRE.sections.length : 0;
    const ex = ($("#example-select") || {}).options ? $("#example-select").options.length - 1 : 0;
    stats.textContent = `${reports} reports · ${sections} intake sections · ${ex} synthetic examples · rule-based, cited, deterministic`;
  }
  try {
    const t = await (await fetch("/static/demo/mcp_transcript.json")).json();
    renderTranscript(t);
  } catch { /* asset optional */ }
}

function renderTranscript(t) {
  const box = $("#mcp-transcript");
  if (!box || !t || !t.steps) return;
  $("#mcp-note").textContent = t.note || "";
  box.innerHTML = "";
  t.steps.forEach((s) => {
    if (s.role === "tool") {
      const card = el("div", { class: "mcp-tool" });
      card.append(el("div", { class: "mcp-tool-head" },
        el("span", { class: "mcp-tool-name" }, `⚙ ${s.name}`),
        el("code", {}, JSON.stringify(s.args))));
      const res = typeof s.result === "string" ? s.result : JSON.stringify(s.result, null, 1);
      card.append(el("pre", { class: "mcp-tool-result" }, res));
      box.append(card);
    } else {
      const bubble = el("div", { class: `mcp-msg mcp-${s.role}` });
      bubble.innerHTML = mdToHtml(s.text || "");
      box.append(el("div", { class: "mcp-row" },
        el("span", { class: "mcp-who" }, s.role === "user" ? "You" : "Claude"), bubble));
    }
  });
}

// --- guided tour: step-by-step, self-paced coach marks ----------------------
//
// A fixed panel (#tour-panel) walks a first-time visitor through the app one
// step at a time. Each step only highlights an element and/or performs its
// action when the visitor presses Next — there are no autoplay timers beyond
// short waits for rendering (fillFields / fetch round-trips).
const tourWait = (ms) => new Promise((r) => setTimeout(r, ms));

function tourFieldTarget(id) {
  // Resolve an input's enclosing .field wrapper (label + help text included)
  // so the highlight reads naturally, falling back to the bare element.
  return () => {
    const n = document.getElementById(id);
    if (!n) return null;
    return n.closest(".field") || n;
  };
}

const TOUR_STEPS = [
  {
    title: "Welcome",
    body: "This is a rule-based EU AI Act companion: the risk tier and every citation come from a deterministic engine, never from a language model. An LLM only <em>drafts</em> free text for you to review. We'll walk through one synthetic health-insurer system, from intake to reports.",
    target: ".howto-steps",
  },
  {
    title: "Load an example",
    body: "This loads a synthetic supplementary health-insurance pricing model into the intake form &mdash; a deployer running a model licensed from a vendor. All data below is fictional.",
    target: "#example-select",
    action: async () => {
      const sel = $("#example-select");
      if (!sel) return;
      sel.value = "health_insurance_pricing";
      sel.dispatchEvent(new Event("change", { bubbles: true }));
      await tourWait(600);
    },
  },
  {
    title: "Where the tier comes from",
    body: "This system falls under Annex III-5, &ldquo;essential services&rdquo;, specifically sub-point 5(c): risk assessment and pricing in life or health insurance. Because it profiles applicants, the narrow Art. 6(3) derogation for non-profiling tasks does not apply, so it stays high-risk.",
    target: tourFieldTarget("hr_usecases"),
  },
  {
    title: "AI assist",
    body: "Free text goes in, a draft questionnaire answer comes out &mdash; you review every field before anything is used. In this sandbox the panel either replays pre-recorded drafts or runs a capped live model; its label says which.",
    target: "#ai-panel",
    skip: () => { const p = $("#ai-panel"); return !p || p.classList.contains("hidden"); },
  },
  {
    title: "Data governance (section 11)",
    body: "Section 11 records the dataset inventory: origin, owner, steward, classification and lawful basis for every dataset feeding the model. AI governance is built on top of this data governance.",
    target: "#dg_datasets",
  },
  {
    title: "Forensic readiness (section 12)",
    body: "Can you evidence afterwards what the model did, with which version and which data? This section covers log scope, retention, integrity and legal hold.",
    target: tourFieldTarget("fr_log_scope"),
  },
  {
    title: "Governance register (section 13)",
    body: "Section 13 tracks who approved this system, the review cadence, any exceptions with an end date, and the Art. 4 AI-literacy record.",
    target: "#gov_exceptions",
  },
  {
    title: "Classify",
    body: "The deterministic engine now classifies the system. Look for the High-risk badge, &ldquo;Applies from 2 Dec 2027&rdquo; (the Digital Omnibus delay), and the finding citing Annex III(5)(c) &mdash; with the note that a FRIA is mandatory for every deployer under 5(c).",
    target: "#result-content",
    action: async () => {
      const already = CURRENT && CURRENT.answers &&
        CURRENT.answers.sys_name === "PolisPrijs supplementary health pricing";
      if (!already) await assess();
      const content = $("#result-content");
      const start = Date.now();
      while (content && !content.children.length && Date.now() - start < 3000) {
        await tourWait(100);
      }
      // showResult() smooth-scrolls to the top; let that finish before the
      // tour scrolls the result block into view, or the two scrolls race.
      await tourWait(1000);
    },
  },
  {
    title: "Reports",
    body: "This is the forensic-readiness report: an evidence register, a readiness score and the parallel reporting clocks. Twenty other tabs cover the remaining reports, the language selector adds a Dutch summary, and the inventory below can export as CSV or an AI register.",
    target: "#report-preview",
    action: async () => { if (CURRENT) await selectReport("forensics"); },
  },
];

const TOUR_STATE = { active: false, index: -1, prevTarget: null };

function tourResolveTarget(step) {
  if (!step || !step.target) return null;
  try {
    return typeof step.target === "function" ? step.target() : $(step.target);
  } catch { return null; }
}

function tourEnsurePanel() {
  let panel = $("#tour-panel");
  if (panel) return panel;
  const title = el("h3", { class: "tour-title", id: "tour-title" });
  const body = el("div", { class: "tour-body", id: "tour-body" });
  const count = el("span", { class: "tour-count", id: "tour-count" });
  const backBtn = el("button", { type: "button", class: "secondary", id: "tour-back", onclick: tourBack }, "Back");
  const nextBtn = el("button", { type: "button", class: "primary", id: "tour-next" }, "Next");
  const closeBtn = el("button", {
    type: "button", class: "tour-close", "aria-label": "Close tour", onclick: () => endTour(),
  }, "×");
  panel = el("div", {
    class: "tour-panel", id: "tour-panel", role: "dialog",
    "aria-live": "polite", "aria-label": "Guided tour", tabindex: "-1",
  }, closeBtn, title, body, el("div", { class: "tour-actions" }, count, backBtn, nextBtn));
  document.body.append(panel);
  return panel;
}

function tourRenderPanel() {
  const step = TOUR_STEPS[TOUR_STATE.index];
  if (!step) return;
  const panel = tourEnsurePanel();
  $("#tour-title").innerHTML = step.title;
  $("#tour-body").innerHTML = step.body;
  $("#tour-count").textContent = `Step ${TOUR_STATE.index + 1} of ${TOUR_STEPS.length}`;
  $("#tour-back").disabled = TOUR_STATE.index === 0;
  const isLast = TOUR_STATE.index === TOUR_STEPS.length - 1;
  const nextBtn = $("#tour-next");
  nextBtn.textContent = isLast ? "Finish" : "Next";
  nextBtn.onclick = isLast
    ? () => endTour({ toastMsg: "Tour finished — try the AI assist or load another example." })
    : tourNext;
  panel.focus();
}

function tourHighlight(step) {
  if (TOUR_STATE.prevTarget) TOUR_STATE.prevTarget.classList.remove("tour-highlight");
  TOUR_STATE.prevTarget = null;
  const target = tourResolveTarget(step);
  if (!target) return;
  target.classList.add("tour-highlight");
  TOUR_STATE.prevTarget = target;
  // Tall targets (a whole report, the result block) start at the top; small
  // ones are centred. Re-scroll once more after render/other scroll effects
  // (assess() and report loading move the page) so the target stays in view.
  const block = target.getBoundingClientRect().height > window.innerHeight * 0.6
    ? "start" : "center";
  target.scrollIntoView({ behavior: "smooth", block });
  // A smooth scroll started elsewhere (showResult() scrolls to the top) can
  // swallow ours; check twice more and jump instantly if the target left view.
  const ensure = () => {
    if (!TOUR_STATE.active || TOUR_STATE.prevTarget !== target) return;
    const r = target.getBoundingClientRect();
    const inView = r.top >= 0 && r.top < window.innerHeight * 0.5;
    if (!inView) target.scrollIntoView({ behavior: "auto", block });
  };
  setTimeout(ensure, 900);
  setTimeout(ensure, 2200);
}

async function tourGo(index, { forward = true } = {}) {
  if (index < 0) return;
  if (index >= TOUR_STEPS.length) {
    endTour({ toastMsg: "Tour finished — try the AI assist or load another example." });
    return;
  }
  const step = TOUR_STEPS[index];
  if (step.skip && step.skip()) {
    tourGo(forward ? index + 1 : index - 1, { forward });
    return;
  }
  TOUR_STATE.index = index;
  if (forward && step.action) {
    try { await step.action(); }
    catch (e) { toast(`Step failed: ${e && e.message ? e.message : e}`); }
  }
  tourRenderPanel();
  tourHighlight(step);
}

function tourNext() { tourGo(TOUR_STATE.index + 1, { forward: true }); }
function tourBack() { tourGo(TOUR_STATE.index - 1, { forward: false }); }

function tourKeyHandler(e) {
  if (!TOUR_STATE.active) return;
  if (e.key === "Escape") { e.preventDefault(); endTour(); return; }
  if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
  if (e.key === "ArrowRight" || e.key === "Enter") { e.preventDefault(); tourNext(); }
  else if (e.key === "ArrowLeft") { e.preventDefault(); if (TOUR_STATE.index > 0) tourBack(); }
}

function startTour() {
  const btn = $("#btn-tour");
  if (btn) btn.disabled = true;
  TOUR_STATE.active = true;
  TOUR_STATE.index = -1;
  TOUR_STATE.prevTarget = null;
  document.addEventListener("keydown", tourKeyHandler);
  tourGo(0, { forward: true });
}

function endTour(opts = {}) {
  TOUR_STATE.active = false;
  document.removeEventListener("keydown", tourKeyHandler);
  if (TOUR_STATE.prevTarget) TOUR_STATE.prevTarget.classList.remove("tour-highlight");
  TOUR_STATE.prevTarget = null;
  const panel = $("#tour-panel");
  if (panel) panel.remove();
  const btn = $("#btn-tour");
  if (btn) btn.disabled = false;
  if (opts.toastMsg) toast(opts.toastMsg);
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
  const prefix = data.fallback_from ? "Live-AI budget reached — this draft was replayed. " : "";
  showAiNotice(
    `<strong>${escapeHtml(prefix + (data.hitl_notice || "AI draft — review every field."))}</strong> ` +
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
  if (!QUESTIONNAIRE) return;
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
  // boolean/radio/multiselect render as a group of inputs inside a <div>, which
  // is not labelable — use a span + aria-labelledby instead of <label for>.
  const isGroup = ["boolean", "radio", "multiselect"].includes(q.type);
  const labelText = [q.label, q.required ? el("span", { class: "req" }, " *") : ""];
  wrap.append(isGroup
    ? el("span", { class: "q", id: `${q.id}-label` }, ...labelText)
    : el("label", { class: "q", for: q.id }, ...labelText));
  const groupProps = (role) => ({ id: q.id, role, "aria-labelledby": `${q.id}-label` });

  let input;
  if (q.type === "text") {
    input = el("input", { type: "text", id: q.id, name: q.id, placeholder: q.placeholder || "" });
  } else if (q.type === "textarea") {
    input = el("textarea", { id: q.id, name: q.id, placeholder: q.placeholder || "" });
  } else if (q.type === "select") {
    input = el("select", { id: q.id, name: q.id });
    input.append(el("option", { value: "" }, "— select —"));
    q.options.forEach((o) => input.append(el("option", { value: o.value }, o.label)));
  } else if (q.type === "boolean") {
    input = el("div", { class: "segmented", ...groupProps("radiogroup") });
    [["true", "Yes"], ["false", "No"]].forEach(([val, lab], i) => {
      input.append(el("label", {},
        el("input", { type: "radio", name: q.id, value: val, ...(i === 1 ? { checked: "checked" } : {}) }),
        el("span", {}, lab)));
    });
  } else if (q.type === "radio") {
    input = el("div", { class: "choice", ...groupProps("radiogroup") });
    q.options.forEach((o) => input.append(el("label", {},
      el("input", { type: "radio", name: q.id, value: o.value }), o.label)));
  } else if (q.type === "multiselect") {
    input = el("div", { class: "choice", ...groupProps("group") });
    q.options.forEach((o) => input.append(el("label", {},
      el("input", { type: "checkbox", name: q.id, value: o.value }), o.label)));
  } else if (q.type === "table") {
    input = renderTableField(q);
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

// --- table question type (repeatable rows, e.g. the dataset inventory) ------
function tableRow(q, values = {}) {
  const tr = el("tr", {});
  q.columns.forEach((c) => {
    let cell;
    if (c.type === "select") {
      cell = el("select", { "data-col": c.id, "aria-label": c.label });
      cell.append(el("option", { value: "" }, "—"));
      (c.options || []).forEach((o) => cell.append(el("option", { value: o.value }, o.label)));
    } else {
      cell = el("input", { type: "text", "data-col": c.id, "aria-label": c.label });
    }
    if (values[c.id] !== undefined && values[c.id] !== null) cell.value = String(values[c.id]);
    tr.append(el("td", {}, cell));
  });
  tr.append(el("td", {}, el("button", {
    type: "button", class: "row-del", title: "Remove row",
    onclick: () => tr.remove(),
  }, "×")));
  return tr;
}

function renderTableField(q) {
  const box = el("div", { class: "dg-table", id: q.id, "data-table": "1" });
  const table = el("table", {},
    el("thead", {}, el("tr", {}, ...q.columns.map((c) => el("th", {}, c.label)), el("th", {}, ""))),
    el("tbody", {}));
  box.append(el("div", { class: "dg-table-scroll" }, table));
  box.append(el("button", {
    type: "button", class: "row-add",
    onclick: () => table.querySelector("tbody").append(tableRow(q)),
  }, "+ Add row"));
  return box;
}

function collectTable(q) {
  const box = document.getElementById(q.id);
  if (!box) return [];
  const rows = [];
  box.querySelectorAll("tbody tr").forEach((tr) => {
    const row = {};
    let any = false;
    tr.querySelectorAll("[data-col]").forEach((cell) => {
      const v = (cell.value || "").trim();
      if (v) { row[cell.dataset.col] = v; any = true; }
    });
    if (any) rows.push(row);
  });
  return rows;
}

function fillTable(q, rows) {
  const box = document.getElementById(q.id);
  if (!box) return;
  const tbody = box.querySelector("tbody");
  tbody.innerHTML = "";
  (Array.isArray(rows) ? rows : []).forEach((r) => {
    if (r && typeof r === "object") tbody.append(tableRow(q, r));
  });
}

function questionById(id) {
  if (!QUESTIONNAIRE) return null;
  for (const s of QUESTIONNAIRE.sections) {
    for (const q of s.questions) if (q.id === id) return q;
  }
  return null;
}

// --- collect answers --------------------------------------------------------
function collectAnswers() {
  const a = {};
  if (!QUESTIONNAIRE) return a;
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
      } else if (q.type === "table") {
        const rows = collectTable(q);
        if (rows.length) a[q.id] = rows;
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
  // CSS.escape: imported/AI-drafted values may contain quotes or backslashes,
  // which would otherwise make querySelector throw mid-import.
  for (const [k, v] of Object.entries(a)) {
    const name = CSS.escape(k);
    const qdef = questionById(k);
    if (qdef && qdef.type === "table") {
      fillTable(qdef, v);
    } else if (Array.isArray(v)) {
      // first clear existing selections of this multiselect
      document.querySelectorAll(`input[name="${name}"]`).forEach((c) => (c.checked = false));
      v.forEach((val) => {
        const c = document.querySelector(`input[name="${name}"][value="${CSS.escape(String(val))}"]`);
        if (c) c.checked = true;
      });
    } else if (typeof v === "boolean") {
      const c = document.querySelector(`input[name="${name}"][value="${v}"]`);
      if (c) c.checked = true;
    } else {
      const node = document.getElementById(k);
      if (node && (node.tagName === "INPUT" || node.tagName === "TEXTAREA" || node.tagName === "SELECT")) {
        node.value = v;
      }
      const radio = document.querySelector(`input[name="${name}"][value="${CSS.escape(String(v))}"]`);
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
      const sevBadge = r.severity
        ? el("span", { class: `sev-badge sev-${String(r.severity).toLowerCase()}` }, r.severity)
        : null;
      const sevLine = r.severity_rationale
        ? el("div", {}, el("em", {}, "Severity: "), `${r.severity} — ${r.severity_rationale}`)
        : null;
      blk.append(el("div", { class: "finding security" },
        el("span", { class: "refs sec" }, r.id),
        sevBadge,
        el("div", {}, el("strong", {}, r.name)),
        el("div", {}, r.summary),
        el("div", { class: "sec-meta" },
          sevLine,
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
  const lang = ($("#report-lang") || {}).value || "en";
  const res = await fetch(`/api/assessments/${CURRENT.id}/report?type=${type}&lang=${lang}`);
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
  let roll;
  try { roll = await (await fetch("/api/portfolio")).json(); }
  catch { toast("Could not load the inventory."); return; }
  const items = roll.systems || [];
  $("#saved-count").textContent = roll.count ?? items.length;
  const list = $("#saved-list");
  list.innerHTML = "";
  if (!items.length) {
    list.append(el("p", { class: "section-desc" }, "No saved assessments yet."));
    return;
  }

  // Portfolio roll-up: risk-tier distribution + obligation/disclosure counts.
  const TIER_LABELS = {
    prohibited: "Prohibited", high: "High", limited: "Limited",
    minimal: "Minimal", unknown: "Unknown",
  };
  const summary = el("div", { class: "inv-rollup" });
  const dist = el("div", { class: "inv-dist" });
  Object.entries(roll.tier_distribution || {})
    .sort((a, b) => b[1] - a[1])
    .forEach(([tier, n]) => dist.append(el("span", {
      class: `tier-badge tier-${tier}`, style: "font-size:.72rem;padding:2px 9px;margin-right:6px;",
    }, `${TIER_LABELS[tier] || tier}: ${n}`)));
  summary.append(dist);
  summary.append(el("p", { class: "section-desc" },
    `${roll.high_risk_count || 0} with high-risk obligations · ` +
    `${roll.art50_count || 0} with an Art. 50 disclosure duty · ` +
    `${roll.overdue_review_count || 0} review(s) overdue · ` +
    `${roll.incomplete_count || 0} with incomplete documentation · ` +
    `${roll.forensic_not_ready_count || 0} not forensic-ready`));
  const next = (roll.due || [])[0];
  if (next) {
    summary.append(el("p", { class: "section-desc" },
      `Next obligations due: ${next.obligations_date} — ${next.sys_name}`));
  }
  list.append(summary);

  const table = el("table", { class: "inv-table" });
  table.append(el("thead", {}, el("tr", {},
    el("th", {}, "System"), el("th", {}, "Risk tier"), el("th", {}, "Due from"),
    el("th", {}, "Art. 50"), el("th", {}, "Security"), el("th", {}, "Evidence"),
    el("th", {}, "Governance"), el("th", {}, "Next review"),
    el("th", {}, "Created"), el("th", {}, "Actions"))));
  const tbody = el("tbody", {});
  items.forEach((it) => {
    const actions = el("td", { class: "inv-actions" });
    // Real buttons (styled as links): href-less <a> is not keyboard-operable.
    actions.append(el("button", { type: "button", class: "linkish",
                                  onclick: () => openSaved(it.id) }, "Open"));
    actions.append(el("button", { type: "button", class: "linkish",
                                  onclick: () => exportJson(it.id) }, "JSON"));
    const del = el("button", { type: "button", class: "linkish danger" }, "Delete");
    del.addEventListener("click", () => confirmDelete(del, it.id));
    actions.append(del);
    tbody.append(el("tr", {},
      el("td", {}, it.sys_name || "(unnamed)"),
      el("td", {}, el("span", {
        class: `tier-badge tier-${it.tier}`, style: "font-size:.72rem;padding:2px 9px;",
      }, it.tier_label || it.tier || "—")),
      el("td", { class: "inv-date" }, it.obligations_date || "—"),
      el("td", {}, it.art50_disclosure ? "Yes" : "—"),
      el("td", {}, String(it.security_risks ?? 0)),
      el("td", { title: it.forensic_band || "" },
        it.forensic_score === undefined ? "—" : `${it.forensic_score}/${it.forensic_max}`),
      el("td", {}, `${it.gov_status || "—"}${it.documentation_complete === false ? " · incomplete" : ""}`),
      el("td", { class: it.review_overdue ? "inv-date overdue" : "inv-date",
                 title: it.review_overdue ? "Review overdue" : "" },
        (it.next_review || "—") + (it.review_overdue ? " !" : "")),
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
  const res = await fetch(`/api/assessments/${id}`);
  if (!res.ok) { toast("Assessment not found."); return; }
  const data = await res.json();
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

function exportRegisterCsv() {
  const a = el("a", { href: "/api/register.csv", download: "ai-register.csv" });
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
  const res = await fetch(`/api/assessments/${id}`);
  if (!res.ok) { toast("Assessment not found."); return; }
  const data = await res.json();
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
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, (_, x) => `<code>${x}</code>`)
    // Only linkify http/https/mailto/anchor URLs — never javascript: etc.
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, text, url) =>
      /^(https?:\/\/|mailto:|#)/i.test(url)
        ? `<a href="${url}" target="_blank" rel="noopener">${text}</a>`
        : m)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    // Word-bounded so bare snake_case ids (arch_api_write) are left alone.
    .replace(/(^|[\s(])_([^_\s][^_]*)_(?=$|[\s.,;:)])/g, "$1<em>$2</em>");
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

    // Paragraph — always consume at least one line: a line containing '|' that
    // is not part of a table would otherwise match no branch and loop forever.
    const buf = [line];
    i++;
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
