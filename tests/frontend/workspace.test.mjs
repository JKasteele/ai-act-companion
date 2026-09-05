import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  freshState,
  restoreState,
  saveAction,
  findingStatus,
  draftRecord,
  apiState,
  addEvent,
} from "../../static/workspace/model.mjs";
const data = JSON.parse(
  readFileSync(
    new URL("../../static/workspace/case.json", import.meta.url),
    "utf8",
  ),
);

test("unknown is preserved across restoration and API serialisation", () => {
  const state = restoreState({
    version: 1,
    data_route: false,
    oversight: "verified",
  });
  assert.equal(state.data_route, "unknown");
  assert.equal(state.oversight, "unknown");
  assert.equal(apiState(state).data_route, "unknown");
  assert.deepEqual(restoreState({ version: 99 }), freshState());
});
test("completion requires evidence and never grants approval", () => {
  const state = freshState();
  assert.throws(
    () =>
      saveAction(state, "data", {
        owner: "Privacy",
        status: "ready_for_review",
        evidence: " ",
      }),
    /evidence/,
  );
  assert.throws(
    () => saveAction(state, "data", { status: "approved" }),
    /status/,
  );
  assert.throws(() => saveAction(state, "__proto__", {}), /Unknown action/);
  saveAction(state, "data", {
    owner: "Privacy",
    status: "ready_for_review",
    evidence: "trace-123",
  });
  assert.equal(findingStatus(state, "data"), "Needs evidence");
});
test("restored unsubstantiated ready status returns to open", () => {
  const state = restoreState({
    version: 1,
    actions: { data: { status: "ready_for_review", evidence: "" } },
  });
  assert.equal(state.actions.data.status, "open");
});
test("clarifications do not silently close findings", () => {
  const state = freshState();
  state.data_route = "redacted";
  state.oversight = "server";
  assert.match(findingStatus(state, "data"), /review open/);
  assert.match(findingStatus(state, "oversight"), /review open/);
  assert.equal(findingStatus(state, "retention"), "Needs evidence");
});
test("record includes provenance, unknowns, owners, and draft status", () => {
  const state = freshState();
  addEvent(state, "Reviewer requested a trace", "2026-09-05T09:00:00Z");
  saveAction(state, "data", {
    owner: "Privacy reviewer",
    status: "in_progress",
    evidence: "Pending",
  });
  const result = draftRecord(data, state);
  for (const expected of [
    "DRAFT",
    "No launch approval",
    "data: unknown",
    "Privacy reviewer",
    "business:data",
    "Reviewer requested a trace",
    "not independently verified",
  ])
    assert.ok(result.includes(expected), expected);
});
test("restoration bounds notes, owner fields, and the activity log", () => {
  const state = restoreState({
    version: 1,
    data_note: "x".repeat(3000),
    actions: { data: { owner: "x".repeat(300), evidence: "x".repeat(3000) } },
    events: Array.from({ length: 70 }, () => ({ label: "Change", at: "now" })),
  });
  assert.equal(state.data_note.length, 2000);
  assert.equal(state.actions.data.owner.length, 200);
  assert.equal(state.actions.data.evidence.length, 2000);
  assert.equal(state.events.length, 50);
});
