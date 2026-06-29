import { access } from "node:fs/promises";
import { constants } from "node:fs";
import { spawn } from "node:child_process";
import { platform } from "node:os";
import { join } from "node:path";

export async function fileExists(path) {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

/** Resolve Chrome/Chromium for Puppeteer and headless PDF export. */
export async function findChrome() {
  if (process.env.CHROME_PATH && (await fileExists(process.env.CHROME_PATH))) {
    return process.env.CHROME_PATH;
  }

  const candidates = [];
  if (platform() === "win32") {
    const pf = process.env["ProgramFiles"] ?? "C:\\Program Files";
    const pf86 = process.env["ProgramFiles(x86)"] ?? "C:\\Program Files (x86)";
    const local = process.env.LOCALAPPDATA ?? "";
    candidates.push(
      join(pf, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
      join(local, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
      join(pf86, "Microsoft", "Edge", "Application", "msedge.exe")
    );
  } else if (platform() === "darwin") {
    candidates.push(
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/Applications/Chromium.app/Contents/MacOS/Chromium"
    );
  } else {
    candidates.push(
      "/usr/local/bin/google-chrome",
      "/usr/bin/google-chrome",
      "/usr/bin/google-chrome-stable",
      "/usr/bin/chromium",
      "/usr/bin/chromium-browser",
      "/snap/bin/chromium"
    );
  }

  for (const path of candidates) {
    if (await fileExists(path)) return path;
  }

  throw new Error(
    "Chrome not found. Install Google Chrome or set CHROME_PATH to your browser executable."
  );
}

export function toFileUrl(path) {
  const normalized = path.replace(/\\/g, "/");
  if (/^[a-zA-Z]:/.test(normalized)) {
    return `file:///${normalized}`;
  }
  return `file://${normalized}`;
}

export async function waitForUrl(url, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return;
    } catch {
      // retry
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`Preview server not available at ${url} after ${timeoutMs / 1000}s`);
}

/** Start `npm run preview` in the background; returns a cleanup function. */
export async function startPreview(port) {
  const url = `http://127.0.0.1:${port}`;
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      console.log(`Preview already running at ${url}`);
      return () => {};
    }
  } catch {
    // not running — start it
  }

  console.log(`Starting preview server on ${url}...`);
  const npmCmd = platform() === "win32" ? "npm.cmd" : "npm";
  const child = spawn(
    npmCmd,
    ["run", "preview", "--", "--host", "127.0.0.1", "--port", String(port)],
    { stdio: "ignore", detached: true, shell: platform() === "win32" }
  );
  child.unref();

  child.on("error", (err) => {
    console.error("Failed to start preview server:", err.message);
  });

  await waitForUrl(url);
  console.log(`Preview ready at ${url}`);

  return () => {
    if (!child.pid) return;
    try {
      if (platform() === "win32") {
        spawn("taskkill", ["/pid", String(child.pid), "/f", "/t"], { stdio: "ignore", shell: true });
      } else {
        process.kill(-child.pid, "SIGTERM");
      }
    } catch {
      try {
        child.kill();
      } catch {
        // already stopped
      }
    }
  };
}
