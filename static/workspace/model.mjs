export const STORAGE_KEY = "ai-act-companion:meridian:v1";
export function freshState() {
  return {
    version: 1,
    data_route: "unknown",
    data_note: "",
    oversight: "unknown",
    oversight_note: "",
    actions: {},
    events: [],
  };
}
const clip = (value, limit) =>
  typeof value === "string" ? value.slice(0, limit) : "";
export function restoreState(raw) {
  const state = freshState();
  if (!raw || raw.version !== 1) return state;
  if (["unknown", "raw", "redacted"].includes(raw.data_route))
    state.data_route = raw.data_route;
  if (["unknown", "prompt", "server"].includes(raw.oversight))
    state.oversight = raw.oversight;
  state.data_note = clip(raw.data_note, 2000);
  state.oversight_note = clip(raw.oversight_note, 2000);
  for (const id of ["data", "oversight", "retention"]) {
    const action = raw.actions?.[id];
    if (!action || typeof action !== "object") continue;
    const status = ["open", "in_progress", "ready_for_review"].includes(
      action.status,
    )
      ? action.status
      : "open";
    const evidence = clip(action.evidence, 2000);
    state.actions[id] = {
      owner: clip(action.owner, 200),
      evidence,
      status:
        status === "ready_for_review" && !evidence.trim() ? "open" : status,
    };
  }
  state.events = Array.isArray(raw.events)
    ? raw.events
        .slice(-50)
        .filter(
          (e) => typeof e?.label === "string" && typeof e?.at === "string",
        )
        .map((e) => ({ label: clip(e.label, 300), at: clip(e.at, 40) }))
    : [];
  return state;
}
export function apiState(state) {
  return {
    data_route: state.data_route,
    data_note: state.data_note,
    oversight: state.oversight,
    oversight_note: state.oversight_note,
    actions: state.actions,
  };
}
export function addEvent(state, label, at = new Date().toISOString()) {
  state.events.push({ label, at });
  state.events = state.events.slice(-50);
}
export function saveAction(state, id, action) {
  if (!["data", "oversight", "retention"].includes(id))
    throw new Error("Unknown action");
  if (!["open", "in_progress", "ready_for_review"].includes(action.status))
    throw new Error("Unknown action status");
  if (action.status === "ready_for_review" && !action.evidence.trim())
    throw new Error(
      "Add a completion-evidence reference before marking this ready for review.",
    );
  state.actions[id] = {
    owner: action.owner.slice(0, 200),
    status: action.status,
    evidence: action.evidence.slice(0, 2000),
  };
}
export function findingStatus(state, id) {
  if (
    (id === "data" && state.data_route !== "unknown") ||
    (id === "oversight" && state.oversight !== "unknown")
  )
    return "Clarified; evidence review open";
  return "Needs evidence";
}
export function draftRecord(data, state, assessment = null) {
  const lines = [
    "# Meridian Health — AI governance review",
    "",
    "**DRAFT — human review required. No launch approval recorded.**",
    "",
    "Fictional organisation; synthetic evidence. This is a portfolio case, not a legal determination.",
    "",
    "## System",
    "",
    "Member service assistant. Answers coverage questions and retrieves claim status for an authenticated member. No coverage, premium, eligibility, or payment decisions.",
    "",
    "The existing pilot is read-only. Proposed contact-detail write access is a separate change.",
    "",
    "## Reviewer clarifications",
    "",
    `- Model-boundary data: ${state.data_route}.`,
    `- Data note: ${state.data_note || "Not supplied."}`,
    `- Approval enforcement: ${state.oversight}.`,
    `- Oversight note: ${state.oversight_note || "Not supplied."}`,
    "",
    "These are reviewer statements, not independently verified implementation evidence.",
    "",
    "## Findings and actions",
    "",
  ];
  for (const finding of data.findings) {
    const action = state.actions[finding.id];
    lines.push(
      `### ${finding.title}`,
      "",
      finding.description,
      "",
      `- Status: ${findingStatus(state, finding.id)}`,
      `- Basis: ${finding.basis} (${finding.basis_source})`,
      `- Sources: ${finding.sources.join(", ")}`,
      `- Action: ${finding.action}`,
      `- Owner: ${action?.owner || finding.owner}`,
      `- Action status: ${action?.status || "open"}`,
      `- Completion evidence supplied: ${action?.evidence || "None."}`,
      `- Evidence needed: ${finding.completion}`,
      "",
    );
  }
  if (assessment)
    lines.push(
      "## Engine result",
      "",
      `- Tier label: ${assessment.classification.tier_label}`,
      `- Knowledge version: ${assessment.knowledge_version}`,
      `- Scope: ${assessment.scope}`,
      `- Provenance: ${assessment.provenance}`,
      "",
      "This result uses the existing synthetic scenario input snapshot. Reviewer notes do not silently change classifier inputs.",
      "",
    );
  lines.push("## Evidence register", "");
  for (const doc of data.documents)
    lines.push(
      `- ${doc.title}, version ${doc.version}, ${doc.date}, owner: ${doc.owner}. Source ID: ${doc.id}.`,
    );
  lines.push("", "## Activity", "");
  for (const event of state.events) lines.push(`- ${event.at}: ${event.label}`);
  return lines.join("\n");
}
