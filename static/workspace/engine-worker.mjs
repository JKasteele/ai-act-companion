import { loadPyodide } from "./runtime/pyodide.mjs";
let runtime;
async function start() {
  const python = await loadPyodide({
    indexURL: new URL("./runtime/", import.meta.url).href,
  });
  const response = await fetch(new URL("./engine.zip", import.meta.url));
  if (!response.ok)
    throw new Error("Assessment engine could not be downloaded.");
  python.unpackArchive(await response.arrayBuffer(), "zip");
  python.runPython("from app.workspace.toolkit import dispatch\nimport json");
  return python;
}
let queue = Promise.resolve();
self.onmessage = ({ data }) => {
  queue = queue
    .catch(() => {})
    .then(async () => {
      try {
        runtime ||= start().catch((error) => {
          runtime = null;
          throw error;
        });
        const python = await runtime;
        python.globals.set("workspace_payload", JSON.stringify(data.payload));
        const result = python.runPython(
          "json.dumps(dispatch(json.loads(workspace_payload)))",
        );
        self.postMessage({ id: data.id, result: JSON.parse(result) });
      } catch (error) {
        self.postMessage({
          id: data.id,
          error: String(error.message || error),
        });
      }
    });
};
