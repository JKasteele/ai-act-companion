import { escapeHTML as esc } from './markdown.mjs';
import { requiredMissing } from './hub-model.mjs';

export function nextWork(system, catalogue) {
  const review = system.review || {};
  const pending = (review.proposals || []).filter(p => p.status === 'pending').length;
  const missing = system.result?.missing?.length || requiredMissing(system.answers, catalogue).length;
  const actions = (review.actions || []).filter(a => a.status !== 'ready_for_review').length;
  const findings = (review.findings || []).length;
  let next = { view: 'documents', title: 'Prepare a draft review pack', detail: 'Bring the assessment, evidence and outstanding work together for human review.' };
  if (!system.result?.classification) next = { view: 'intake', title: 'Complete the remaining screening', detail: `${missing} recorded screening gaps. Conditional questions may require further answers; no risk tier is inferred.` };
  if (actions && system.result?.classification) next = { view: 'actions', title: 'Follow up on the open actions', detail: `${actions} actions still need work. A ready-for-review status does not verify a control.` };
  if (pending) next = { view: 'proposals', title: 'Review the source-linked answers', detail: `${pending} proposals await your judgment. Compare the current and proposed answers before accepting.` };
  if (findings && !(review.decisions || []).length) next = { view: 'findings', title: 'Compare the evidence behind the findings', detail: 'Read the original passages and record what remains uncertain before progressing the review.' };
  if (!system.evidence?.length && !system.result?.classification) next = { view: 'evidence', title: 'Add the evidence you have', detail: 'Attach a text document or note, or continue the screening manually. Missing evidence remains unknown.' };
  return { ...next, pending, missing, actions, findings };
}
export function workPlan(system, catalogue) {
  const n = nextWork(system, catalogue);
  return `<section class="next-work"><div><p class="context">Suggested next step</p><h2>${esc(n.title)}</h2><p>${esc(n.detail)}</p><button class="button primary" data-action="${n.view}">Continue review</button></div><dl class="work-counts"><div><dt>Screening gaps</dt><dd>${n.missing}</dd></div><div><dt>Evidence findings</dt><dd>${n.findings}</dd></div><div><dt>Pending proposals</dt><dd>${n.pending}</dd></div><div><dt>Actions needing work</dt><dd>${n.actions}</dd></div></dl></section>`;
}
export const tourSteps = [
  ['overview', 'Understand the decision', 'Read the Meridian brief. You are reviewing an expansion of a member-service assistant, not granting launch approval.'],
  ['findings', 'Compare the evidence', 'Compare the business and architecture passages. What information actually reaches the model?'],
  ['proposals', 'Review an answer', 'Inspect a quotation and accept or skip a proposed answer. Unanswered screening questions remain open.'],
  ['actions', 'Record the follow-up', 'Assign an action and record a review note explaining what evidence is still needed.'],
  ['documents', 'Prepare the handoff', 'Export the review pack. With incomplete screening it is a work-in-progress record; complete screening separately to attach engine reports.'],
];
export function tourPanel(system, view) {
  if (!system.review?.tour) return '';
  const i = tourSteps.findIndex(s => s[0] === view);
  const step = tourSteps[Math.max(0, i)];
  return `<section class="review-tour" aria-label="Five-minute review"><div class="section-heading"><strong>Meridian review · about 5 minutes</strong><button class="text-link" data-action="reset-tour">Reset this demo</button></div><nav aria-label="Review walkthrough">${tourSteps.map(([v, label], index) => `<a href="#system/${system.id}/${v}" ${v === view ? 'aria-current="step"' : ''}><span>${index + 1}</span>${label}</a>`).join('')}</nav><p>${esc(step[2])}</p><div class="toolbar">${i < 4 ? `<button class="button secondary" data-action="${tourSteps[Math.max(0, i) + 1][0]}">Next: ${tourSteps[Math.max(0, i) + 1][1]}</button>` : '<button class="button primary" data-action="review-pack">Prepare review pack</button>'}<small>Steps guide navigation; they do not certify completion.</small></div></section>`;
}
export function recommendedReports(system, catalogue) {
  const scenario = (catalogue.scenarios || []).find(c => c.id === system?.review?.caseId);
  return scenario?.reports || ['risk', 'security', 'governance'];
}
