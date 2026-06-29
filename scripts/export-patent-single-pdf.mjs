#!/usr/bin/env node
/**
 * Export a single docs/patents/*.md counsel brief to standalone PDF.
 * Usage: node scripts/export-patent-single-pdf.mjs <source.md> <output-basename>
 */
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { findChrome, toFileUrl } from "./patent-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");

function mdToHtml(md) {
  let html = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  html = html.replace(/```([\s\S]*?)```/g, (_, code) => `<pre><code>${code.trim()}</code></pre>`);
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  html = html.replace(/^\|(.+)\|$/gm, (line) => {
    const cells = line.split("|").filter(Boolean).map((c) => c.trim());
    if (cells.every((c) => /^-+$/.test(c))) return "";
    const isHeader = cells.some((c) => /^\*\*/.test(c));
    const tag = isHeader ? "th" : "td";
    return `<tr>${cells.map((c) => `<${tag}>${c.replace(/\*\*/g, "")}</${tag}>`).join("")}</tr>`;
  });
  html = html.replace(/((?:<tr>.*<\/tr>\n?)+)/g, "<table>$1</table>");

  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

  html = html
    .split(/\n{2,}/)
    .map((block) => {
      const t = block.trim();
      if (!t) return "";
      if (/^<(h[1-4]|ul|table|pre)/.test(t)) return t;
      return `<p>${t.replace(/\n/g, "<br/>")}</p>`;
    })
    .join("\n");

  return html;
}

async function chromePdf(chromePath, htmlPath, pdfPath) {
  return new Promise((resolve, reject) => {
    const proc = spawn(chromePath, [
      "--headless=new",
      "--disable-gpu",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-extensions",
      "--run-all-compositor-stages-before-draw",
      "--virtual-time-budget=10000",
      `--print-to-pdf=${pdfPath}`,
      htmlPath,
    ], { stdio: "inherit" });

    let settled = false;
    const finish = (err) => {
      if (settled) return;
      settled = true;
      clearInterval(poll);
      clearTimeout(timer);
      err ? reject(err) : resolve();
    };

    const poll = setInterval(async () => {
      try {
        const st = await stat(pdfPath);
        if (st.size > 1000) {
          try { proc.kill(); } catch { /* ignore */ }
          finish();
        }
      } catch { /* ignore */ }
    }, 2000);

    const timer = setTimeout(async () => {
      try {
        const st = await stat(pdfPath);
        if (st.size > 1000) {
          try { proc.kill("SIGKILL"); } catch { /* ignore */ }
          finish();
          return;
        }
      } catch { /* ignore */ }
      try { proc.kill("SIGKILL"); } catch { /* ignore */ }
      finish(new Error("Chrome PDF timed out"));
    }, 90000);

    proc.on("close", (code) => {
      if (settled) return;
      code === 0 ? finish() : finish(new Error(`Chrome exit ${code}`));
    });
    proc.on("error", (err) => finish(err));
  });
}

async function main() {
  const srcArg = process.argv[2];
  const baseArg = process.argv[3];
  if (!srcArg || !baseArg) {
    console.error("Usage: node scripts/export-patent-single-pdf.mjs <source.md> <output-basename>");
    process.exit(1);
  }

  const SRC = join(ROOT, srcArg);
  const DIST = join(ROOT, "docs/patents/dist");
  const HTML_OUT = join(DIST, `${baseArg}.html`);
  const PDF_OUT = join(DIST, `${baseArg}.pdf`);
  const title = basename(baseArg).replace(/-/g, " ");

  await mkdir(DIST, { recursive: true });
  const md = await readFile(SRC, "utf8");

  const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>${title}</title>
  <style>
    body { font-family: Georgia, 'Times New Roman', serif; max-width: 8.5in; margin: 0 auto; padding: 0.75in; color: #111; line-height: 1.45; font-size: 11pt; }
    h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 6px; }
    h2 { font-size: 14pt; margin-top: 1.2em; page-break-after: avoid; }
    h3 { font-size: 12pt; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
    th, td { border: 1px solid #999; padding: 6px 8px; vertical-align: top; text-align: left; }
    th { background: #f0f0f0; }
    pre { background: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 9pt; white-space: pre-wrap; }
    code { font-family: Consolas, monospace; font-size: 9.5pt; }
    ul { margin: 8px 0; }
    @media print { body { padding: 0.5in; } }
  </style>
</head>
<body>${mdToHtml(md)}</body>
</html>`;

  await writeFile(HTML_OUT, fullHtml, "utf8");
  console.log(`Wrote ${HTML_OUT}`);

  const chromePath = await findChrome();
  await chromePdf(chromePath, toFileUrl(HTML_OUT), PDF_OUT);
  console.log(`Wrote ${PDF_OUT}`);
}

main().catch((err) => {
  console.error(err.message ?? err);
  process.exit(1);
});
