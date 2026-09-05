// Conservative renderer: HTML is escaped and only http(s) links are clickable.
export const escapeHTML = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function inline(text) {
  return escapeHTML(text)
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noreferrer">$1</a>',
    )
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}
export function markdownHTML(markdown) {
  const lines = markdown.split(/\r?\n/);
  let html = "",
    table = false,
    list = false,
    code = false;
  const close = () => {
    if (table) {
      html += "</tbody></table>";
      table = false;
    }
    if (list) {
      html += "</ul>";
      list = false;
    }
  };
  for (const line of lines) {
    if (line.startsWith("```")) {
      close();
      html += code ? "</code></pre>" : "<pre><code>";
      code = !code;
      continue;
    }
    if (code) {
      html += escapeHTML(line) + "\n";
      continue;
    }
    if (/^\|/.test(line)) {
      if (list) {
        html += "</ul>";
        list = false;
      }
      if (/^\|[\s:|\-]+\|?$/.test(line)) continue;
      const cells = line.replace(/^\||\|$/g, "").split(/(?<!\\)\|/);
      if (!table) {
        html += "<table><tbody>";
        table = true;
      }
      html +=
        "<tr>" +
        cells.map((c) => `<td>${inline(c.trim())}</td>`).join("") +
        "</tr>";
      continue;
    }
    if (/^[-*] /.test(line)) {
      if (table) {
        html += "</tbody></table>";
        table = false;
      }
      if (!list) {
        html += "<ul>";
        list = true;
      }
      html += `<li>${inline(line.slice(2))}</li>`;
      continue;
    }
    close();
    const heading = line.match(/^(#{1,6}) (.*)$/);
    if (heading)
      html += `<h${heading[1].length}>${inline(heading[2])}</h${heading[1].length}>`;
    else if (line.startsWith("> "))
      html += `<blockquote>${inline(line.slice(2))}</blockquote>`;
    else if (line.trim()) html += `<p>${inline(line)}</p>`;
  }
  close();
  if (code) html += "</code></pre>";
  return html;
}
