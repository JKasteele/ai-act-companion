import { test } from "node:test";
import assert from "node:assert/strict";
import {
  newSystem,
  importSystem,
  restoreInventory,
} from "../../static/workspace/hub-model.mjs";
import {
  startCase,
  acceptProposal,
  saveAction,
  sourceNote,
  reviewPack,
  cleanReview,
} from "../../static/workspace/casework-model.mjs";
import {
  scenarioCards,
  scenarioBrief,
  proposalsView,
  actionsView,
} from "../../static/workspace/casework.mjs";
const scenario = {
  id: "test",
  name: "Assistant",
  organisation: "Test Company",
  sector: "Infrastructure",
  owner: "Operations",
  date: "2026-09-04",
  brief: "Fictional review",
  decision: "Can the trial proceed?",
  documents: [
    {
      id: "brief",
      title: "Charter",
      owner: "Operations",
      version: "1",
      date: "2026-09-01",
      sections: [
        { id: "purpose", title: "Purpose", text: "We deploy a vendor model." },
      ],
    },
  ],
  findings: [
    {
      id: "gap",
      title: "Scope is incomplete",
      description: "Need details",
      sources: ["brief:purpose"],
      owner: "Operations",
      action: "Confirm scope",
      completion: "Reviewed charter",
      priority: "High",
    },
  ],
  proposals: [
    {
      field: "provider_role",
      value: "deployer",
      source: "brief:purpose",
      quote: "We deploy a vendor model.",
      reason: "Owner statement",
    },
  ],
};
const working = () =>
  startCase(newSystem({ sys_name: "Test" }, "test"), scenario);

test("starting a case copies evidence and leaves every proposed answer pending", () => {
  const s = working();
  assert.equal(s.answers.provider_role, undefined);
  assert.equal(s.result, null);
  assert.equal(s.review.proposals[0].status, "pending");
  assert.equal(s.review.actions[0].status, "open");
  assert.equal(
    sourceNote(s, s.review.findings[0].sources[0]).text,
    "We deploy a vendor model.",
  );
  s.evidence[0].text = "Changed";
  assert.equal(
    scenario.documents[0].sections[0].text,
    "We deploy a vendor model.",
  );
});
test("accepting one grounded proposal invalidates classification; changed sources block acceptance", () => {
  const s = working();
  s.result = { classification: { tier: "minimal" } };
  acceptProposal(s, 0);
  assert.equal(s.answers.provider_role, "deployer");
  assert.equal(s.result, null);
  assert.equal(s.review.proposals[0].status, "accepted");
  assert.throws(() => acceptProposal(s, 0));
  const changed = working();
  changed.evidence[0].text = "Unknown";
  assert.throws(() => acceptProposal(changed, 0));
});
test("ready for review requires an owner and evidence and never resolves the finding", () => {
  const s = working();
  assert.throws(() => saveAction(s, 0, { status: "approved" }));
  assert.throws(() =>
    saveAction(s, 0, {
      status: "ready_for_review",
      owner: "Operations",
      evidence: " ",
    }),
  );
  assert.throws(() =>
    saveAction(s, 0, {
      status: "ready_for_review",
      owner: "",
      evidence: "trace",
    }),
  );
  saveAction(s, 0, {
    status: "ready_for_review",
    owner: "Operations",
    evidence: "simulator-trace-12",
  });
  assert.equal(s.review.actions[0].status, "ready_for_review");
  assert.equal(s.review.findings[0].status, undefined);
  assert.equal(
    cleanReview({
      actions: [{ title: "test", status: "ready_for_review", evidence: "" }],
    }).actions[0].status,
    "open",
  );
});
test("export/import and restoration retain review work without trusting a classification", () => {
  const s = working();
  s.review.decisions.push({
    reviewer: "Security",
    note: "More evidence needed",
    at: "2026-09-04",
  });
  s.result = { classification: { tier: "minimal" } };
  const imported = importSystem(JSON.parse(JSON.stringify(s)), "imported");
  assert.equal(imported.result, null);
  assert.deepEqual(imported.review, s.review);
  const [restored] = restoreInventory({ version: 1, systems: [s] });
  assert.deepEqual(restored.review, s.review);
});
test("review pack includes provenance, unknowns, actions and human notes", () => {
  const s = working();
  s.review.decisions.push({
    reviewer: "Security",
    note: "No trial decision yet",
    at: "2026-09-04",
  });
  const pack = reviewPack(s);
  assert.ok(pack.includes("Not classified"));
  assert.ok(pack.includes("Authored scenario finding"));
  assert.ok(pack.includes("Reviewed charter"));
  assert.ok(pack.includes("No trial decision yet"));
  assert.ok(pack.includes("No launch approval"));
  assert.ok(
    reviewPack(s, [{ markdown: "# Engine draft" }]).includes("# Engine draft"),
  );
});
test("case views expose real sources and escape document content", () => {
  const c = structuredClone(scenario);
  c.documents[0].sections[0].text = "<script>bad</script>";
  assert.ok(!scenarioBrief(c).includes("<script>"));
  assert.ok(scenarioCards([c]).includes("#case/test"));
  const s = working(),
    catalogue = {
      questionnaire: {
        sections: [{ questions: [{ id: "provider_role", label: "Role" }] }],
      },
    };
  assert.ok(
    proposalsView(s, catalogue, false).includes("#system/test/evidence/0"),
  );
  assert.ok(actionsView(s).includes("Ready for evidence review"));
});
