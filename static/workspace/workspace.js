import { riskClass } from "./risk-style.mjs";
import {
  STORAGE_KEY,
  freshState,
  restoreState,
  apiState,
  addEvent,
  saveAction,
  findingStatus,
  draftRecord,
} from "./model.mjs";

const $ = (selector) => document.querySelector(selector);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const main = $("#main");
const overviewHTML = main.innerHTML;
let data,
  assessment = null,
  backend = false,
  busy = false,
  toastTimer;
let state = freshState();
let storageAvailable = true;
try {
  state = restoreState(JSON.parse(localStorage.getItem(STORAGE_KEY)));
} catch {
  storageAvailable = false;
}

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    storageAvailable = false;
  }
  $("#connection-status").textContent = storageAvailable
    ? "Review saved on this device"
    : "Session only · export to keep";
}
function toast(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("#toast").hidden = true), 4200);
}
function sourceButton(id) {
  const [docId] = id.split(":");
  const doc = data.documents.find((d) => d.id === docId);
  return `<button class="source-link" data-source="${esc(id)}">${esc(doc?.title || id)} ↗</button>`;
}
function heading(title, description, context = "Meridian Health") {
  return `<div class="page-heading"><div><p class="context">${esc(context)}</p><h1>${esc(title)}</h1><p class="subheading">${esc(description)}</p></div></div>`;
}
function message(text, options = {}) {
  const el = document.createElement("div");
  el.className = `agent-message${options.user ? " user" : ""}`;
  el.innerHTML = `${!options.user ? `<span class="message-label">${options.live ? "Companion · live AI draft" : "Companion · guided walkthrough"}</span>` : ""}${text
    .split("\n\n")
    .map((p) => `<p>${esc(p)}</p>`)
    .join(
      "",
    )}${(options.events || []).map((e) => `<div class="tool-event">✓ ${esc(e.label)}</div>`).join("")}${(options.sources || []).map(sourceButton).join("")}${options.action ? `<button class="suggestion" data-action="${esc(options.action)}">${esc(options.label)} ↗</button>` : ""}`;
  $("#messages").append(el);
  el.scrollIntoView({ block: "nearest" });
}
function documentView(sourceId) {
  const [docId, sectionId] = sourceId.split(":");
  const doc = data.documents.find((d) => d.id === docId);
  if (!doc) return;
  $("#evidence-content").innerHTML =
    `<h2 id="evidence-title">${esc(doc.title)}</h2><p class="subheading">Version ${esc(doc.version)} · ${esc(doc.owner)} · ${esc(doc.date)}</p><p class="notice">Synthetic source document, authored for this case.</p>${doc.sections.map((s) => `<section class="document-section${sectionId === s.id ? " highlight" : ""}"><h3>${esc(s.title)}</h3><p>${esc(s.text)}</p><small>${esc(doc.id)}:${esc(s.id)}</small></section>`).join("")}`;
  $("#evidence-dialog").showModal();
  $("#evidence-dialog .highlight")?.scrollIntoView({ block: "nearest" });
}
function renderEvidence() {
  return (
    heading(
      "Evidence library",
      "Four sources. One shared record of what is known and what still needs checking.",
    ) +
    `<div class="evidence-grid">${data.documents.map((doc) => `<button class="evidence-card" data-source="${esc(doc.id)}"><div class="source-meta"><span>${esc(doc.kind)}</span><span>v${esc(doc.version)}</span></div><h3>${esc(doc.title)}</h3><p>${esc(doc.summary)}</p><div class="source-meta"><span>${esc(doc.owner)}</span><span>Open document ↗</span></div></button>`).join("")}</div>`
  );
}
function quote(id) {
  const [d, s] = id.split(":");
  const doc = data.documents.find((doc) => doc.id === d);
  const section = doc.sections.find((section) => section.id === s);
  return `<div class="quote-card${d === "architecture" ? " conflict" : ""}"><div class="source-meta"><strong>${esc(doc.title)}</strong><span>v${esc(doc.version)}</span></div><blockquote>“${esc(section.text)}”</blockquote>${sourceButton(id)}</div>`;
}
function renderInvestigation(kind = "data") {
  const finding = data.findings.find((f) => f.id === kind);
  const isData = kind === "data";
  const value = isData ? state.data_route : state.oversight;
  const options = isData
    ? [
        ["raw", "The full claim-status payload reaches the model"],
        ["redacted", "The payload is redacted before it reaches the model"],
        ["unknown", "I don’t know yet; request implementation evidence"],
      ]
    : [
        ["prompt", "Approval currently relies on the agent prompt"],
        ["server", "The server checks approval before executing the tool"],
        ["unknown", "I don’t know yet; request implementation evidence"],
      ];
  return (
    heading(
      isData
        ? "Where does the claim data go?"
        : "What enforces human approval?",
      finding.description,
      isData
        ? "Investigate the data gap"
        : "Investigate the proposed write tool",
    ) +
    `<div class="comparison">${finding.sources.map(quote).join("")}</div><div class="review-box"><h2>${isData ? "Record your clarification" : "Record how approval works"}</h2><p>A clarification records your understanding. Supporting evidence still needs review.</p><form id="clarification-form" data-kind="${kind}"><fieldset style="border:0;padding:0;margin:0"><legend class="review-note">${isData ? "Which statement describes the implementation?" : "Which statement describes the approval boundary?"}</legend><div class="choices">${options.map(([v, label]) => `<label class="choice"><input type="radio" name="clarification" value="${v}"${value === v ? " checked" : ""}>${esc(label)}</label>`).join("")}</div></fieldset><label class="review-note" for="clarification-note">Evidence reference or reviewer note (optional)</label><textarea id="clarification-note" class="record-block" maxlength="2000" rows="2" style="width:100%;margin:0;padding:10px" placeholder="For example: request a redacted request trace from engineering">${esc(isData ? state.data_note : state.oversight_note)}</textarea><button type="submit" class="button primary">Save clarification</button><span class="review-note">Saved on this device. This does not close the finding or approve launch.</span></form></div>`
  );
}
function renderFindings() {
  return (
    heading(
      "Findings",
      "Follow each concern back to its sources, review criterion, and proposed action.",
    ) +
    `<div class="notice">These three findings are authored into the guided case. Live AI may explain the evidence; it cannot close findings.</div>${data.findings.map((f) => `<section class="finding-detail"><span class="status-pill ${f.id === "data" ? "amber" : "blue"}">${esc(f.kind)}</span><h3>${esc(f.title)}</h3><p>${esc(f.description)}</p><div>${f.sources.map(sourceButton).join("")}</div><p><strong>Review basis:</strong> ${esc(f.basis)} ${sourceButton(f.basis_source)}</p><p><strong>Next action:</strong> ${esc(f.action)}</p><div class="section-heading"><span class="progress-label">${esc(findingStatus(state, f.id))}</span><button class="text-link" data-action="${f.id === "data" ? "investigate" : f.id}">Investigate</button></div></section>`).join("")}`
  );
}
function renderActions() {
  return (
    heading(
      "Action plan",
      "Give each gap an owner and a clear definition of the evidence needed for review.",
    ) +
    data.findings
      .map((f) => {
        const a = state.actions[f.id] || {};
        return `<form class="action-card" data-action-form="${esc(f.id)}"><span class="context">${esc(f.kind)}</span><h3>${esc(f.title)}</h3><p>${esc(f.action)}</p><p><strong>Ready when:</strong> ${esc(f.completion)}</p><div class="action-fields"><div><label for="owner-${f.id}">Accountable owner</label><input id="owner-${f.id}" name="owner" maxlength="200" value="${esc(a.owner || f.owner)}"></div><div><label for="status-${f.id}">Action status</label><select id="status-${f.id}" name="status">${[
          ["open", "Open"],
          ["in_progress", "In progress"],
          ["ready_for_review", "Ready for evidence review"],
        ]
          .map(
            ([v, l]) =>
              `<option value="${v}"${(a.status || "open") === v ? " selected" : ""}>${l}</option>`,
          )
          .join(
            "",
          )}</select></div></div><label for="evidence-${f.id}">Completion-evidence reference</label><textarea id="evidence-${f.id}" name="evidence" maxlength="2000" placeholder="Reference a test, document, or reviewer decision. A reference is not automatically verified.">${esc(a.evidence || "")}</textarea><div class="toolbar"><button class="button secondary" type="submit">Save action</button></div></form>`;
      })
      .join("")
  );
}
function renderRecord() {
  return (
    heading(
      "Review record",
      "A portable draft that keeps findings, evidence, and human decisions together.",
    ) +
    `<div class="toolbar"><button class="button primary" data-action="export">Download review draft</button><button class="button secondary" data-action="engine">Inspect engine profile</button></div><pre class="record-block">${esc(draftRecord(data, state, assessment))}</pre>`
  );
}
function renderEngine() {
  return (
    heading(
      "Inspect the assessment profile",
      "Run the existing rule engine on the synthetic read-only pilot. Proposed write access remains a separate review.",
    ) +
    `<div class="review-box"><h2>Confirm the scenario inputs</h2><p>The supplied profile describes an EU health-insurer deployer using a hosted model for coverage questions and claim-status retrieval. It interacts with members, handles personal and health data, and has no authority to decide coverage or payment.</p><p>The current pilot uses per-user, read-only API access. The fictional evidence pack raises unresolved data-flow, oversight, and retention questions.</p><p><strong>This is a curated example profile.</strong> It is not automatically reconstructed from your conversation or clarifications. The classifier applies the repository’s versioned rules; those rules still require independent legal review.</p><button class="button primary" data-action="run-engine">Confirm profile & ${backend ? "run engine" : "view computed result"}</button></div>${assessment ? `<section class="review-box"><span class="status-pill ${riskClass(assessment.classification)}">${esc(assessment.classification.tier_label)} · scenario result</span><h2 style="margin-top:15px">Deterministic assessment</h2><p>${esc(assessment.scope)}</p><p>${esc(assessment.provenance)}</p><p>Knowledge version: ${esc(assessment.knowledge_version)}</p><details class="trace-detail"><summary>Inspect the structured result and exact inputs</summary><pre>${esc(JSON.stringify(assessment, null, 2))}</pre></details><button class="text-link" data-action="record">Include in the review record</button></section>` : ""}`
  );
}
function renderAbout() {
  return (
    heading(
      "Governance you can inspect",
      "AI Act Companion · a portfolio project by Jesse van de Kasteele",
    ) +
    `<article class="about-copy"><p>This workspace explores how an AI assistant can support an accountable governance review: collect evidence, expose uncertainty, investigate technical controls, and prepare useful work for a human decision.</p><h2>Try the case</h2><p>Compare the business proposal with the architecture notes. Record a clarification, assign the follow-up action, and export the draft review record. Then investigate what changes when the assistant gains write access.</p><h2>Two honest modes</h2><p><strong>Guided walkthrough:</strong> curated findings and scripted explanations, available without a model. It demonstrates the workflow; it does not claim to discover new issues.</p><p><strong>Live AI:</strong> available in the local FastAPI app when an existing Ollama or Anthropic provider is configured. The model chooses read-only evidence tools and explains its findings. Requests are bounded and citations are checked against sources actually read. The hosted preview is the guided walkthrough.</p><h2>Evidence and decisions stay separate</h2><p>Unknowns remain unknown. Reviewer statements are labelled as statements. A task can become ready for evidence review, but this demo never grants launch approval or automatically verifies a control.</p><h2>The existing assessment engine</h2><p>The Python classifier and security toolkit remain available through the web app, CLI, and MCP. This workspace can run the existing synthetic read-only scenario and expose the exact inputs and versioned result.</p><div class="toolbar"><button class="button primary" data-action="investigate">Explore the case</button><a class="button secondary" href="https://github.com/JKasteele/ai-act-companion" target="_blank" rel="noreferrer">Explore the repository ↗</a>${backend ? '<a class="text-link" href="/classic">Open the original toolkit</a>' : ""}</div></article>`
  );
}
function render() {
  if (!data) return;
  const view = location.hash.slice(1) || "overview";
  const renderers = {
    overview: () => overviewHTML,
    evidence: renderEvidence,
    findings: renderFindings,
    actions: renderActions,
    record: renderRecord,
    investigate: () => renderInvestigation("data"),
    oversight: () => renderInvestigation("oversight"),
    about: renderAbout,
    engine: renderEngine,
  };
  main.innerHTML = (renderers[view] || renderers.overview)();
  document.querySelectorAll("[data-view]").forEach((el) => {
    const active =
      el.dataset.view === view ||
      (["investigate", "oversight"].includes(view) &&
        el.dataset.view === "findings");
    el.classList.toggle("active", active);
    if (active) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
  if (view === "overview" && state.data_route !== "unknown") {
    $(".decision-banner h2").textContent =
      "Clarification recorded. Evidence review is next.";
    $(".decision-banner p").textContent =
      "Your understanding of the data flow is saved. The finding remains open until supporting evidence and the corresponding action are reviewed.";
  }
}
function navigate(view) {
  if (location.hash === "#" + view) render();
  else location.hash = view;
}
function investigate(kind = "data", narrate = true) {
  navigate(
    kind === "data"
      ? "investigate"
      : kind === "oversight"
        ? "oversight"
        : "findings",
  );
  if (!narrate) return;
  if (kind === "data")
    message(
      "The business proposal says no health data reaches the model. The architecture says the full claim-status response—including treatment details—is appended to the model context. Both statements cannot describe the same data flow.\n\nWhich describes the implementation? If you don’t know, keep it unknown and request a payload trace.",
      { sources: ["business:data", "architecture:payload"] },
    );
  else if (kind === "oversight")
    message(
      "The current pilot is read-only. The proposed write tool introduces a different question: what prevents an unapproved change?\n\nAn approval instruction in a prompt does not demonstrate server-side enforcement. Ask for a rejected unapproved-call test and the approval-to-execution trace.",
      { sources: ["architecture:permissions", "governance:controls"] },
    );
  else
    message(
      "The fictional vendor guide describes 30-day default logging and an optional reduction. That does not tell us which setting applies to this account.\n\nRequest account-specific configuration and record the responsible owner’s retention decision.",
      {
        sources: ["vendor:retention", "governance:gate"],
        action: "actions",
        label: "Assign the retention action",
      },
    );
}
async function action(name) {
  if (!data) return;
  if (name === "investigate") return investigate("data");
  if (name === "oversight" || name === "retention") return investigate(name);
  if (name === "reset") {
    if (busy) {
      toast("Wait for the current response before resetting.");
      return;
    }
    state = freshState();
    assessment = null;
    persist();
    $("#messages").innerHTML = "";
    message(
      "The case is reset. Start by comparing the business proposal and architecture notes.",
      { action: "investigate", label: "Compare the evidence" },
    );
    navigate("overview");
    toast("Demo case reset on this device.");
    return;
  }
  if (name === "export") {
    const url = URL.createObjectURL(
      new Blob([draftRecord(data, state, assessment)], {
        type: "text/markdown;charset=utf-8",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "meridian-health-review-draft.md";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Review draft downloaded.");
    return;
  }
  if (name === "run-engine") {
    try {
      const response = backend
        ? await fetch("/api/workspace/assess", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirm_synthetic_profile: true }),
          })
        : await fetch("./assessment.json");
      if (!response.ok)
        throw new Error("The assessment is unavailable. Please retry.");
      assessment = await response.json();
      if (!backend)
        assessment.provenance +=
          " This hosted walkthrough displays a build-time snapshot, not a live Python call.";
      addEvent(
        state,
        "Confirmed the read-only scenario profile and inspected its engine result.",
      );
      persist();
      render();
      message(
        `The scenario engine result is ${assessment.classification.tier_label}. It describes the supplied read-only pilot, not the proposed write-enabled change. The three evidence findings remain open.`,
        { action: "record", label: "Open the draft record" },
      );
    } catch (error) {
      toast(error.message);
    }
    return;
  }
  navigate(name);
}
document.addEventListener("click", (event) => {
  const source = event.target.closest("[data-source]");
  if (source && data) {
    documentView(source.dataset.source);
    return;
  }
  const button = event.target.closest("[data-action]");
  if (button) action(button.dataset.action);
});
document.addEventListener("submit", async (event) => {
  if (event.target.id === "clarification-form") {
    event.preventDefault();
    const form = event.target;
    const kind = form.dataset.kind;
    const selected = new FormData(form).get("clarification");
    const note = $("#clarification-note").value;
    if (kind === "data") {
      state.data_route = selected;
      state.data_note = note;
    } else {
      state.oversight = selected;
      state.oversight_note = note;
    }
    addEvent(
      state,
      `${kind === "data" ? "Data flow" : "Approval enforcement"} clarification recorded as ${selected}; evidence review remains open.`,
    );
    persist();
    toast("Clarification saved. Evidence review remains open.");
    message(
      selected === "unknown"
        ? "Unknown is recorded explicitly. The next useful step is to request the missing implementation evidence and assign its owner."
        : "Your clarification is recorded as a reviewer statement. It does not override the source documents or verify the implementation. I’ve kept the evidence finding open.",
      { action: "actions", label: "Prepare the follow-up action" },
    );
  } else if (event.target.matches("[data-action-form]")) {
    event.preventDefault();
    const form = event.target;
    const values = new FormData(form);
    try {
      saveAction(state, form.dataset.actionForm, {
        owner: values.get("owner"),
        status: values.get("status"),
        evidence: values.get("evidence"),
      });
      addEvent(
        state,
        `Updated ${form.dataset.actionForm} action: ${values.get("status")}.`,
      );
      persist();
      toast("Action saved.");
    } catch (error) {
      toast(error.message);
    }
  }
});
$("#chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!data || busy) return;
  const input = $("#message");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  message(text, { user: true });
  if (!$("#live-mode").checked) {
    const q = text.toLowerCase();
    if (/approv|oversight|write|tool|secur|permission/.test(q))
      investigate("oversight");
    else if (/retention|vendor|logging|region/.test(q))
      investigate("retention");
    else if (/report|export|record|document/.test(q)) {
      navigate("record");
      message(
        "The review record brings together the case evidence, your clarifications, and the action plan. It remains a draft for human review.",
        { action: "export", label: "Download the draft" },
      );
    } else if (/classif|tier|legal|risk/.test(q)) {
      navigate("engine");
      message(
        "Risk classification comes from the existing rule engine. Review the supplied scenario profile before inspecting its result. The proposed write tool is a separate change.",
        { action: "engine", label: "Inspect the profile" },
      );
    } else if (/data|claim|privacy|first|start|gap|conflict|next/.test(q))
      investigate("data");
    else
      message(
        "This is the guided walkthrough, with a fixed synthetic case. I can take you through the data conflict, approval enforcement, retention, or the review record. Free-form model reasoning is available through Live AI in a configured local app.",
        { action: "investigate", label: "Investigate the data conflict" },
      );
    return;
  }
  busy = true;
  $(".send-button").disabled = true;
  $("#live-mode").disabled = true;
  const pending = document.createElement("div");
  pending.className = "tool-event";
  pending.textContent = "Companion is investigating the case evidence…";
  $("#messages").append(pending);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 240000);
  try {
    const response = await fetch("/api/workspace/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, state: apiState(state) }),
      signal: controller.signal,
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "The live request could not be completed.",
      );
    message(result.answer, {
      live: true,
      sources: result.sources,
      events: result.events,
    });
  } catch (error) {
    message(
      error.name === "AbortError"
        ? "The request timed out. The server may still finish its bounded request; your review has not changed. You can switch to the guided walkthrough."
        : error.message,
    );
  } finally {
    clearTimeout(timeout);
    pending.remove();
    busy = false;
    $(".send-button").disabled = false;
    $("#live-mode").disabled = false;
  }
});
$("#live-mode").addEventListener("change", () => {
  $("#agent-mode").textContent = $("#live-mode").checked
    ? `Live AI · ${data.provider} · drafts only`
    : "Guided demo · no live model";
});
$("#reset").addEventListener("click", () => action("reset"));
$("#close-evidence").addEventListener("click", () =>
  $("#evidence-dialog").close(),
);
$("#evidence-dialog").addEventListener("click", (event) => {
  if (event.target === $("#evidence-dialog")) {
    const rect = event.target.getBoundingClientRect();
    if (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    )
      event.target.close();
  }
});
window.addEventListener("hashchange", () => {
  render();
  main.focus({ preventScroll: true });
});

async function init() {
  try {
    // API detection is skipped by the static export marker; no model is called.
    const config = await fetch("./mode.json")
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
    if (!config?.static) {
      try {
        const r = await fetch("/api/workspace/case");
        if (
          r.ok &&
          r.headers.get("content-type")?.includes("application/json")
        ) {
          data = await r.json();
          backend = true;
        }
      } catch {
        /* The exported guided case remains available. */
      }
    }
    if (!data) {
      const r = await fetch("./case.json");
      if (!r.ok)
        throw new Error(
          "Case evidence could not be loaded. Reload the page or start the local app.",
        );
      data = await r.json();
    }
    $("#live-mode").disabled = !backend || !data.live_configured;
    $("#live-mode").title =
      backend && data.live_configured
        ? "Use the configured model to investigate this synthetic case. Provider charges may apply."
        : "Live AI requires the local app and a configured Ollama or Anthropic provider.";
    $("#connection-status").textContent = storageAvailable
      ? "Review stays on this device"
      : "Session only · export to keep";
    render();
  } catch (error) {
    main.innerHTML =
      heading("The case could not be opened", error.message) +
      '<button class="button primary" onclick="location.reload()">Reload workspace</button>';
    $("#connection-status").textContent = "Case unavailable";
  }
}
init();
