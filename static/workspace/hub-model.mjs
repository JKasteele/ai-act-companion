import { cleanReview } from "./casework-model.mjs";
export const INVENTORY_KEY = "ai-act-companion:systems:v1";
export function newSystem(answers = {}, id = crypto.randomUUID()) {
  return {
    id,
    answers: structuredClone(answers),
    result: null,
    evidence: [],
    activity: [],
    review: cleanReview(),
    updated: new Date().toISOString(),
  };
}
export function updateAnswers(system, answers) {
  system.answers = structuredClone(answers);
  system.result = null;
  system.updated = new Date().toISOString();
  log(system, "Updated system profile; previous assessment invalidated.");
}
export function log(system, label) {
  if (system.activity.at(-1)?.label === label) {
    system.activity[system.activity.length - 1].at = new Date().toISOString();
    return;
  }
  system.activity = [
    ...system.activity,
    { at: new Date().toISOString(), label },
  ].slice(-100);
}
export function importSystem(raw, id) {
  const answers = raw?.answers || raw;
  if (
    !answers ||
    typeof answers !== "object" ||
    Array.isArray(answers) ||
    typeof answers.sys_name !== "string" ||
    !answers.sys_name.trim()
  )
    throw new Error(
      "Import an assessment or answer object with a system name.",
    );
  if (JSON.stringify(answers).length > 100000)
    throw new Error("The imported answer set is too large.");
  const system = newSystem(answers, id);
  system.evidence = cleanEvidence(raw?.evidence);
  system.activity = cleanActivity(raw?.activity);
  system.review = cleanReview(raw?.review);
  log(system, "Imported as a draft; classification requires review.");
  return system;
}
function cleanEvidence(raw) {
  return Array.isArray(raw)
    ? raw
        .filter(
          (e) => typeof e?.title === "string" && typeof e?.text === "string",
        )
        .slice(0, 30)
        .map((e) => ({
          title: e.title.slice(0, 200),
          text: e.text.slice(0, 10000),
          reference:
            typeof e.reference === "string" ? e.reference.slice(0, 300) : "",
        }))
    : [];
}
function cleanActivity(raw) {
  return Array.isArray(raw)
    ? raw
        .filter(
          (e) => typeof e?.label === "string" && typeof e?.at === "string",
        )
        .slice(-100)
        .map((e) => ({ label: e.label.slice(0, 500), at: e.at.slice(0, 100) }))
    : [];
}
export function restoreInventory(raw) {
  if (raw?.version !== 1 || !Array.isArray(raw.systems)) return [];
  return raw.systems
    .slice(0, 100)
    .filter(
      (s) =>
        typeof s?.id === "string" &&
        /^[a-zA-Z0-9-]{1,80}$/.test(s.id) &&
        s.answers &&
        typeof s.answers === "object" &&
        !Array.isArray(s.answers) &&
        JSON.stringify(s).length < 2000000,
    )
    .map((s) => ({
      ...newSystem(s.answers, s.id),
      result: s.result && typeof s.result === "object" ? s.result : null,
      updated: typeof s.updated === "string" ? s.updated : "",
      evidence: cleanEvidence(s.evidence),
      activity: cleanActivity(s.activity),
      review: cleanReview(s.review),
    }));
}
export function requiredMissing(answers, catalogue) {
  return catalogue.screening.filter(
    (id) =>
      answers[id] === undefined ||
      answers[id] === null ||
      answers[id] === "" ||
      (Array.isArray(answers[id]) && !answers[id].length),
  );
}
export function routeIntent(text) {
  const q = text.toLowerCase();
  if (/next|action|task|follow.up/.test(q)) return { view: "actions" };
  if (/intake|propos|extract/.test(q)) return { view: "proposals" };
  if (/dpia|privacy impact/.test(q))
    return { view: "documents", report: "dpia" };
  if (/red.?team/.test(q)) return { view: "documents", report: "redteam" };
  if (/security|threat|control|bias|forensic/.test(q))
    return { view: "findings" };
  if (/report|document|fria|governance register/.test(q))
    return { view: "documents" };
  if (/example|demo/.test(q)) return { view: "examples" };
  if (/evidence|source/.test(q)) return { view: "evidence" };
  if (/assess|new system|we use|we are|we build/.test(q))
    return { view: "new" };
  return { view: "overview" };
}
export function csvRegister(systems) {
  const escape = (v) => {
    let text = String(v ?? "");
    if (/^[=+@\-\t\r]/.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  return [
    ["System", "Owner", "Status", "Risk tier", "Updated"],
    ...systems.map((s) => [
      s.answers.sys_name,
      s.answers.sys_owner,
      s.result?.status || "Draft",
      s.result?.classification?.tier_label || "Not assessed",
      s.updated,
    ]),
  ]
    .map((row) => row.map(escape).join(","))
    .join("\r\n");
}
