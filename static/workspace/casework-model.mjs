const text = (v, max = 1000) => (typeof v === "string" ? v.slice(0, max) : "");
export const statuses = ["open", "in_progress", "ready_for_review"];
export function cleanReview(raw = {}) {
  raw ||= {};
  return {
    caseId: text(raw.caseId, 80),
    findings: (Array.isArray(raw.findings) ? raw.findings : [])
      .filter((f) => f && typeof f.title === "string")
      .slice(0, 30)
      .map((f) => ({
        id: text(f.id, 80),
        title: text(f.title, 200),
        description: text(f.description, 3000),
        priority: text(f.priority, 80),
        basis: text(f.basis, 300),
        sources: (Array.isArray(f.sources) ? f.sources : [])
          .filter((s) => typeof s === "string")
          .slice(0, 10)
          .map((s) => s.slice(0, 100)),
        provenance: text(f.provenance, 150),
      })),
    proposals: (Array.isArray(raw.proposals) ? raw.proposals : [])
      .filter(
        (p) =>
          p && typeof p.field === "string" && JSON.stringify(p).length < 12000,
      )
      .slice(0, 50)
      .map((p) => ({
        field: text(p.field, 100),
        value: structuredClone(p.value ?? null),
        source: text(p.source, 100),
        quote: text(p.quote, 1000),
        reason: text(p.reason, 1000),
        status: ["accepted", "rejected"].includes(p.status)
          ? p.status
          : "pending",
        provenance: text(p.provenance, 150),
      })),
    actions: (Array.isArray(raw.actions) ? raw.actions : [])
      .filter((a) => a && typeof a.title === "string")
      .slice(0, 50)
      .map((a) => ({
        id: text(a.id, 80),
        title: text(a.title, 2000),
        owner: text(a.owner, 200),
        priority: ["High", "Medium", "Low"].includes(a.priority)
          ? a.priority
          : "High",
        completion: text(a.completion, 2000),
        evidence: text(a.evidence, 2000),
        due: /^\d{4}-\d{2}-\d{2}$/.test(a.due || "") ? a.due : "",
        status:
          statuses.includes(a.status) &&
          (a.status !== "ready_for_review" ||
            (text(a.evidence).trim() && text(a.owner).trim()))
            ? a.status
            : "open",
      })),
    decisions: (Array.isArray(raw.decisions) ? raw.decisions : [])
      .filter((d) => d && typeof d.note === "string")
      .slice(-30)
      .map((d) => ({
        reviewer: text(d.reviewer, 200),
        note: text(d.note, 2000),
        at: text(d.at, 100),
      })),
  };
}
export function startCase(system, scenario) {
  const sourceMap = new Map();
  system.evidence = scenario.documents.flatMap((d) =>
    d.sections.map((s) => {
      sourceMap.set(`${d.id}:${s.id}`, `evidence${sourceMap.size}:passage`);
      return {
        title: `${d.title} — ${s.title}`,
        text: s.text,
        reference: `${d.id}:${s.id} | ${d.owner} | v${d.version} | ${d.date} | Fictional source`,
      };
    }),
  );
  system.review = cleanReview({
    caseId: scenario.id,
    findings: scenario.findings.map((f) => ({
      ...f,
      sources: f.sources.map((s) => sourceMap.get(s)),
      provenance: "Authored scenario finding",
    })),
    proposals: scenario.proposals.map((p) => ({
      ...p,
      source: sourceMap.get(p.source),
      provenance: "Authored intake proposal",
    })),
    actions: scenario.findings.map((f) => ({
      id: f.id,
      title: f.action,
      owner: f.owner,
      priority: "High",
      completion: f.completion,
      status: "open",
    })),
  });
  return system;
}
export function sourceNote(system, source) {
  const match = /^evidence(\d+):passage$/.exec(source);
  return match
    ? system.evidence[Number(match[1])]
    : source === "system:profile"
      ? {
          title: "Recorded profile",
          text: JSON.stringify(system.answers),
          reference: "Reviewer-provided structured answers",
        }
      : null;
}
export function acceptProposal(system, index) {
  const p = system.review.proposals[index];
  const source = sourceNote(system, p?.source || "");
  if (
    !p ||
    p.status !== "pending" ||
    !p.quote ||
    !source?.text.includes(p.quote)
  )
    throw new Error(
      "The quoted source is missing or changed. Review the evidence before applying this proposal.",
    );
  p.status = "accepted";
  system.answers = { ...system.answers, [p.field]: structuredClone(p.value) };
  system.result = null;
}
export function saveAction(system, index, patch) {
  const action = system.review.actions[index];
  if (!action) throw new Error("Action not found.");
  if (!statuses.includes(patch.status))
    throw new Error("Choose an available review status.");
  if (
    patch.status === "ready_for_review" &&
    (!patch.evidence?.trim() || !patch.owner?.trim())
  )
    throw new Error(
      "Add an owner and evidence reference before marking this ready for review.",
    );
  Object.assign(
    action,
    cleanReview({ actions: [{ ...action, ...patch }] }).actions[0],
  );
}
const md = (v) =>
  String(v ?? "").replace(/[\\`*_{}\[\]<>|#]/g, (c) => "\\" + c);
export function reviewPack(system, reports = []) {
  const r = cleanReview(system.review),
    lines = [
      `# ${md(system.answers.sys_name)} — review pack`,
      "> Draft for human review. No launch approval or control verification is granted by this export.",
      `Generated: ${new Date().toISOString()}`,
      `Accountable owner: ${md(system.answers.sys_owner || "Not assigned")}`,
      `Assessment: ${md(system.result?.classification?.tier_label || "Not classified — screening/review remains incomplete")}`,
      `Knowledge version: ${md(system.result?.knowledge_version || "Not recorded")}`,
      "## System context",
      md(system.answers.sys_description || ""),
      "## Recorded assessment inputs",
      ...Object.entries(system.answers).map(
        ([k, v]) =>
          `- ${md(k)}: ${md(typeof v === "object" ? JSON.stringify(v) : v)}`,
      ),
      "## Evidence register",
    ];
  system.evidence.forEach((e, i) =>
    lines.push(
      `### Source ${i + 1}: ${md(e.title)}`,
      md(e.reference),
      md(e.text),
    ),
  );
  lines.push(
    "## Review findings",
    "Scenario findings are authored; they remain open pending human evidence review.",
  );
  r.findings.forEach((f) =>
    lines.push(
      `### ${md(f.title)}`,
      md(f.description),
      `Basis: ${md(f.basis)}`,
      `Provenance: ${md(f.provenance)}`,
      `Sources: ${md(f.sources.join(", "))}`,
    ),
  );
  lines.push("## Intake proposals");
  r.proposals.forEach((p) =>
    lines.push(
      `- ${md(p.field)} = ${md(JSON.stringify(p.value))} — ${md(p.status)}; ${md(p.provenance)}; ${md(p.source)}. Quote: ${md(p.quote)}`,
    ),
  );
  lines.push("## Follow-up actions");
  r.actions.forEach((a) =>
    lines.push(
      `### ${md(a.title)}`,
      `Owner: ${md(a.owner || "Not assigned")} · Priority: ${md(a.priority)} · Due: ${md(a.due || "Not set")}`,
      `Status: ${md(a.status)} — ready for review does not mean verified.`,
      `Required evidence: ${md(a.completion)}`,
      `Submitted evidence: ${md(a.evidence || "Not supplied")}`,
    ),
  );
  lines.push("## Human review notes");
  r.decisions.forEach((d) =>
    lines.push(`${md(d.at)} — ${md(d.reviewer)}`, md(d.note)),
  );
  if (!r.decisions.length) lines.push("No human review note recorded.");
  lines.push(
    "## Activity",
    ...system.activity.map((a) => `- ${md(a.at)}: ${md(a.label)}`),
  );
  for (const report of reports) lines.push("---", report.markdown);
  if (!reports.length)
    lines.push(
      "## Engine documents",
      "Not attached. Complete screening and run the assessment to include the recommended engine reports.",
    );
  return lines.join("\n\n") + "\n";
}
