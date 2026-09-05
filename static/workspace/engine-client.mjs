let worker,
  serial = 0;
const pending = new Map();
export function browserEngine(payload) {
  if (!worker) {
    worker = new Worker(new URL("./engine-worker.mjs", import.meta.url), {
      type: "module",
    });
    worker.onmessage = ({ data }) => {
      const item = pending.get(data.id);
      if (!item) return;
      clearTimeout(item.timer);
      pending.delete(data.id);
      data.error
        ? item.reject(new Error(data.error))
        : item.resolve(data.result);
    };
    worker.onerror = () =>
      reset(
        "The browser engine could not start. Retry the operation or use the local app.",
      );
  }
  return new Promise((resolve, reject) => {
    const id = ++serial;
    const timer = setTimeout(
      () => reset("The assessment engine timed out. Retry the operation."),
      120000,
    );
    pending.set(id, { resolve, reject, timer });
    worker.postMessage({ id, payload });
  });
}
function reset(message) {
  worker?.terminate();
  worker = null;
  for (const item of pending.values()) {
    clearTimeout(item.timer);
    item.reject(new Error(message));
  }
  pending.clear();
}
