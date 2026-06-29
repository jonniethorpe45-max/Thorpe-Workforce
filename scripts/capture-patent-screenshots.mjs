#!/usr/bin/env node
/**
 * Capture patent documentation screenshots from Thorpe web preview.
 * Requires: npm run build, vite preview running on PATENT_PREVIEW_URL (default http://127.0.0.1:4173)
 */
import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";
import { findChrome } from "./patent-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const OUT_DIR = join(ROOT, "docs/patents/screenshots");
const BASE_URL = process.env.PATENT_PREVIEW_URL ?? "http://127.0.0.1:4173";

const CAPTURES = [
  { file: "01-dashboard.png", path: "/", waitFor: /welcome back/i },
  {
    file: "02-jonathan-chat-wifi.png",
    path: "/jonathan",
    waitFor: /jonathan/i,
    actions: async (page) => {
      const input = await page.waitForSelector('input[placeholder*="IT issue" i], textarea', { timeout: 15000 });
      await input.type("wifi not working");
      await page.keyboard.press("Enter");
      await page.waitForFunction(
        () => document.body.textContent?.match(/offline connectivity|approval needed|diagnostic/i),
        { timeout: 25000 }
      );
      await new Promise((r) => setTimeout(r, 1500));
    },
  },
  {
    file: "03-jonathan-pending-approval.png",
    path: "/jonathan",
    waitFor: /jonathan/i,
    actions: async (page) => {
      const input = await page.waitForSelector('input[placeholder*="IT issue" i], textarea', { timeout: 15000 });
      await input.type("my computer is slow");
      await page.keyboard.press("Enter");
      await page.waitForFunction(
        () => document.body.textContent?.match(/clean temporary|approval needed|approve/i),
        { timeout: 25000 }
      );
      await new Promise((r) => setTimeout(r, 1500));
    },
  },
  {
    file: "04-settings-watchdog.png",
    path: "/settings",
    waitFor: /proactive watchdog/i,
    actions: async (page) => {
      await page.evaluate(() => {
        const headings = Array.from(document.querySelectorAll("h2, h3"));
        const wd = headings.find((h) => /proactive watchdog/i.test(h.textContent ?? ""));
        wd?.scrollIntoView({ block: "center" });
      });
      await new Promise((r) => setTimeout(r, 500));
    },
  },
  {
    file: "05-repair-center.png",
    path: "/repairs",
    waitFor: /repair center/i,
  },
  {
    file: "06-connectivity-report.png",
    path: "/jonathan",
    waitFor: /jonathan/i,
    actions: async (page) => {
      const input = await page.waitForSelector('input[placeholder*="IT issue" i], textarea', { timeout: 15000 });
      await input.type("wifi not working no internet");
      await page.keyboard.press("Enter");
      await page.waitForFunction(
        () => document.body.textContent?.match(/offline connectivity|connectivity check/i),
        { timeout: 25000 }
      );
      await new Promise((r) => setTimeout(r, 2000));
    },
  },
];

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const chromePath = await findChrome();
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    defaultViewport: { width: 1280, height: 800 },
  });

  const page = await browser.newPage();

  for (const cap of CAPTURES) {
    const url = `${BASE_URL}${cap.path}`;
    console.log(`Capturing ${cap.file} ← ${url}`);
    await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
    await page.waitForFunction(
      (pattern) => new RegExp(pattern, "i").test(document.body.textContent ?? ""),
      { timeout: 20000 },
      cap.waitFor.source ?? String(cap.waitFor)
    );
    if (cap.actions) {
      await cap.actions(page);
    }
    await page.screenshot({ path: join(OUT_DIR, cap.file), fullPage: false });
  }

  await browser.close();
  console.log(`Screenshots saved to ${OUT_DIR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
