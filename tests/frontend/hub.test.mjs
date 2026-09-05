import { test } from "node:test";
import assert from "node:assert/strict";
import {
  newSystem,
  updateAnswers,
  importSystem,
  restoreInventory,
  requiredMissing,
  routeIntent,
  csvRegister,
} from "../../static/workspace/hub-model.mjs";
import { markdownHTML } from "../../static/workspace/markdown.mjs";

test("editing clones the inputs and invalidates previous classification", () => {
  const answers = {
    sys_name: "Draft",
    eu_market: false,
    hr_usecases: ["none"],
  };
  const system = newSystem(answers, "test");
  system.result = { classification: { tier: "minimal" } };
  updateAnswers(system, { ...answers, eu_market: true });
  assert.equal(system.result, null);
  assert.equal(answers.eu_market, false);
  assert.equal(system.activity.length, 1);
  assert.deepEqual(
    requiredMissing(answers, {
      screening: ["eu_market", "gpai_model", "hr_usecases"],
    }),
    ["gpai_model"],
  );
});

test("portable exports restore evidence but never trust an imported result or identity", () => {
  const imported = importSystem(
    {
      id: "old",
      source: "example",
      answers: { sys_name: "Test" },
      result: { classification: { tier: "minimal" } },
      evidence: [{ title: "Source", text: "Passage", reference: "Doc 1" }],
      activity: [],
    },
    "new",
  );
  assert.equal(imported.id, "new");
  assert.equal(imported.source, undefined);
  assert.equal(imported.result, null);
  assert.equal(imported.evidence[0].text, "Passage");
  const restored = restoreInventory({
    version: 1,
    systems: [imported, { id: "../invalid", answers: {} }],
  });
  assert.equal(restored.length, 1);
  assert.deepEqual(restored[0].evidence, imported.evidence);
  assert.deepEqual(restoreInventory({ version: 2, systems: [imported] }), []);
  for (const raw of [
    null,
    [],
    { sys_name: " " },
    { sys_name: "x", large: "x".repeat(100000) },
  ])
    assert.throws(() => importSystem(raw));
});

test("malformed saved entries are filtered and evidence notes bounded", () => {
  const system = newSystem({ sys_name: "Test" }, "test");
  system.source = "server";
  system.evidence = [
    null,
    { title: "x", text: "a".repeat(20000), reference: 42 },
  ];
  const [restored] = restoreInventory({ version: 1, systems: [null, system] });
  assert.equal(restored.source, undefined);
  assert.equal(restored.evidence.length, 1);
  assert.equal(restored.evidence[0].text.length, 10000);
  assert.equal(restored.evidence[0].reference, "");
});

test("workflow guidance chooses relevant work without claiming an assessment", () => {
  assert.deepEqual(routeIntent("Prepare a DPIA"), {
    view: "documents",
    report: "dpia",
  });
  assert.equal(routeIntent("Review security threats").view, "findings");
  assert.equal(routeIntent("Compare sources").view, "evidence");
  assert.equal(routeIntent("Show examples").view, "examples");
  assert.equal(routeIntent("We build a new system").view, "new");
});

test("report display escapes embedded HTML and blocks executable links", () => {
  const html = markdownHTML(
    '# Draft\n<img src=x onerror=alert(1)>\n[bad](javascript:alert(1))\n[Source](https://example.org/?x="onmouseover=alert(1))\n**Review**\n| A | B |\n|---|---|\n| one | two |\n- Task\n```\n<script>\n```',
  );
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes('href="javascript:'));
  assert.ok(html.includes("&quot;"));
  assert.ok(html.includes("<strong>Review</strong>"));
  assert.ok(html.includes("<table>"));
  assert.ok(html.includes("<li>Task</li>"));
});

test("register export quotes data and neutralises formula cells", () => {
  const csv = csvRegister([
    newSystem({ sys_name: '=HYPERLINK("x")', sys_owner: "Team, A" }, "test"),
  ]);
  assert.ok(csv.includes('"\'=HYPERLINK(""x"")"'));
  assert.ok(csv.includes('"Team, A"'));
  assert.ok(csv.includes("Not assessed"));
});
