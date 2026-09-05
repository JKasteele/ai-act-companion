// Executes the shipped WebAssembly Python runtime in Node, without browser UI automation.
import { loadPyodide } from "pyodide";
import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
async function main() {
  const python = await loadPyodide();
  python.unpackArchive(
    new Uint8Array(readFileSync("static/workspace/engine.zip")),
    "zip",
  );
  python.runPython(
    "from app.workspace.toolkit import dispatch, catalogue\nimport json",
  );
  const browserCatalogue = JSON.parse(
    python.runPython("json.dumps(catalogue())"),
  );
  const nativeCatalogue = JSON.parse(
    readFileSync("static/workspace/catalogue.json", "utf8"),
  );
  assert.deepEqual(browserCatalogue, nativeCatalogue);
  let reports = 0;
  for (const example of nativeCatalogue.examples) {
    for (const report of nativeCatalogue.reports) {
      python.globals.set(
        "request_json",
        JSON.stringify({
          operation: "example_report",
          example_id: example.id,
          report_type: report.id,
        }),
      );
      const result = JSON.parse(
        python.runPython("json.dumps(dispatch(json.loads(request_json)))"),
      );
      assert.ok(result.markdown.length > 100, `${example.id}/${report.id}`);
      assert.equal(result.draft, true);
      reports++;
    }
  }
  python.globals.set(
    "request_json",
    JSON.stringify({
      operation: "assess",
      answers: { sys_name: "Unknown system" },
    }),
  );
  assert.equal(
    JSON.parse(
      python.runPython("json.dumps(dispatch(json.loads(request_json)))"),
    ).classification,
    null,
  );
  console.log(
    `Browser Python matches the native catalogue: ${nativeCatalogue.examples.length} systems; ${reports} reports generated; unknown-input gate passed.`,
  );
}
main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
