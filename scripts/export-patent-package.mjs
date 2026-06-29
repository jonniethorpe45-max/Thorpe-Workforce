#!/usr/bin/env node
/**
 * Build a single HTML patent package and optional PDF via headless Chrome.
 */
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { promisify } from "node:util";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const PATENTS = join(ROOT, "docs/patents");
const DIST = join(PATENTS, "dist");
const CHROME = process.env.CHROME_PATH ?? "/usr/local/bin/google-chrome";

const ORDER = [
  "00-PATENT-PACKAGE-INDEX.md",
  "07-EXECUTIVE-BRIEF-ONE-PAGE.md",
  "08-ATTORNEY-TRANSMITTAL-LETTER.md",
  "01-INVENTION-DISCLOSURE-JONATHAN.md",
  "02-PATENT-CANDIDATE-INVENTORY.md",
  "03-SYSTEM-ARCHITECTURE-AND-FLOWS.md",
  "04-CLAIM-SEEDS-FOR-ATTORNEY.md",
  "05-PRIOR-ART-DIFFERENTIATION.md",
  "06-INVENTOR-AND-ASSIGNMENT-SHEET.md",
  "09-FIGURE-SCREENSHOT-GUIDE.md",
];

function mdToHtml(md) {
  let html = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Fenced code blocks (incl mermaid as pre)
  html = html.replace(/```([\s\S]*?)```/g, (_, code) => `<pre><code>${code.trim()}</code></pre>`);

  // Headers
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold / inline code
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Tables (simple)
  html = html.replace(/^\|(.+)\|$/gm, (line) => {
    const cells = line.split("|").filter(Boolean).map((c) => c.trim());
    if (cells.every((c) => /^-+$/.test(c))) return "";
    return `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  });
  html = html.replace(/((?:<tr>.*<\/tr>\n?)+)/g, "<table>$1</table>");

  // Lists
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

  // Paragraphs
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

async function embedScreenshots(html) {
  const shotsDir = join(PATENTS, "screenshots");
  const files = [
    "01-dashboard.png",
    "02-jonathan-chat-wifi.png",
    "03-jonathan-pending-approval.png",
    "04-settings-watchdog.png",
    "05-repair-center.png",
    "06-connectivity-report.png",
  ];
  let gallery = "<h2>Appendix — UI Screenshots</h2>";
  for (const file of files) {
    try {
      const buf = await readFile(join(shotsDir, file));
      const b64 = buf.toString("base64");
      gallery += `<figure><img src="data:image/png;base64,${b64}" alt="${file}" style="max-width:100%;border:1px solid #ccc;margin:12px 0"/><figcaption>${file}</figcaption></figure>`;
    } catch {
      gallery += `<p><em>Screenshot not generated: ${file}</em></p>`;
    }
  }
  return html + gallery;
}

async function chromePdf(htmlPath, pdfPath) {
  return new Promise((resolve, reject) => {
    const proc = spawn(
      CHROME,
      [
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        `--print-to-pdf=${pdfPath}`,
        htmlPath,
      ],
      { stdio: "inherit" }
    );
    const timer = setTimeout(() => {
      proc.kill("SIGKILL");
      reject(new Error("Chrome PDF timed out after 60s"));
    }, 60000);
    proc.on("close", (code) => {
      clearTimeout(timer);
      code === 0 ? resolve() : reject(new Error(`Chrome exit ${code}`));
    });
  });
}

async function main() {
  await mkdir(DIST, { recursive: true });

  let body = "";
  for (const file of ORDER) {
    const md = await readFile(join(PATENTS, file), "utf8");
    body += `<section class="doc-section">${mdToHtml(md)}</section><hr/>`;
  }

  const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Thorpe Desktop Patent Package</title>
  <style>
    body { font-family: Georgia, 'Times New Roman', serif; max-width: 8.5in; margin: 0 auto; padding: 0.75in; color: #111; line-height: 1.45; font-size: 11pt; }
    h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 6px; page-break-before: always; }
    h1:first-child { page-break-before: avoid; }
    h2 { font-size: 14pt; margin-top: 1.2em; }
    h3 { font-size: 12pt; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
    td { border: 1px solid #999; padding: 6px 8px; vertical-align: top; }
    pre { background: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 9pt; white-space: pre-wrap; }
    code { font-family: Consolas, monospace; font-size: 9.5pt; }
    hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
    figure { page-break-inside: avoid; }
    figcaption { font-size: 9pt; color: #555; margin-bottom: 16px; }
    @media print { body { padding: 0.5in; } }
  </style>
</head>
<body>
${await embedScreenshots(body)}
</body>
</html>`;

  const htmlPath = join(DIST, "Thorpe-Desktop-Patent-Package.html");
  const pdfPath = join(DIST, "Thorpe-Desktop-Patent-Package.pdf");
  await writeFile(htmlPath, fullHtml, "utf8");
  console.log(`Wrote ${htmlPath}`);

  try {
    await chromePdf(`file://${htmlPath}`, pdfPath);
    console.log(`Wrote ${pdfPath}`);
  } catch (err) {
    console.warn("PDF generation skipped:", err.message);
    console.warn("Open the HTML file in a browser and Print → Save as PDF.");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
