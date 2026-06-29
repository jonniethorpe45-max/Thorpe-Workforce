#!/usr/bin/env node
/**
 * Cross-platform patent package build (Windows, macOS, Linux).
 * Builds frontend, starts preview, captures screenshots, exports HTML/PDF.
 */
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { platform } from "node:os";
import { findChrome, startPreview } from "./patent-utils.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const PREVIEW_PORT = process.env.PATENT_PREVIEW_PORT ?? "4173";
const PREVIEW_URL = `http://127.0.0.1:${PREVIEW_PORT}`;

function run(cmd, args, env = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, {
      cwd: ROOT,
      stdio: "inherit",
      env: { ...process.env, ...env },
      shell: platform() === "win32",
    });
    proc.on("close", (code) =>
      code === 0 ? resolve() : reject(new Error(`${cmd} ${args.join(" ")} exited ${code}`))
    );
    proc.on("error", reject);
  });
}

async function main() {
  const npmCmd = platform() === "win32" ? "npm.cmd" : "npm";

  console.log("==> Installing puppeteer-core (screenshot script)...");
  await run(npmCmd, ["install", "--no-save", "puppeteer-core@23.11.1"]);

  console.log("==> Building frontend...");
  await run(npmCmd, ["run", "build"]);

  const chromePath = await findChrome();
  console.log(`==> Using browser: ${chromePath}`);

  const stopPreview = await startPreview(PREVIEW_PORT);

  try {
    console.log("==> Capturing screenshots...");
    await run(
      process.execPath,
      ["scripts/capture-patent-screenshots.mjs"],
      { CHROME_PATH: chromePath, PATENT_PREVIEW_URL: PREVIEW_URL }
    );

    console.log("==> Exporting combined HTML/PDF...");
    await run(process.execPath, ["scripts/export-patent-package.mjs"], {
      CHROME_PATH: chromePath,
    });
  } finally {
    await stopPreview();
  }

  console.log("");
  console.log("Patent package ready:");
  console.log("  docs/patents/dist/Thorpe-Desktop-Patent-Package.html");
  console.log("  docs/patents/dist/Thorpe-Desktop-Patent-Package.pdf (if Chrome PDF succeeded)");
  console.log("  docs/patents/screenshots/*.png");
  console.log("");
  console.log("Submit docs/patents/ folder + dist PDF to patent counsel.");
}

main().catch((err) => {
  console.error(err.message ?? err);
  process.exit(1);
});
