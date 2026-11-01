import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, join } from "node:path";

import { chromium, expect, test } from "@playwright/test";

const require = createRequire(import.meta.url);
// Lighthouse CI's command line, run with this Node; it drives Playwright's Chromium itself.
const LHCI = require.resolve("@lhci/cli/src/cli.js");
/** Playwright's Chromium in its headless-only build ("headless shell"), which it installs beside the full one. The full
 * browser fails to start on some Windows installations (a side-by-side error, see the Phase 5 report); this one runs. */
function headlessShell(): string {
  const full = chromium.executablePath(); // …/ms-playwright/chromium-1248/chrome-win64/chrome.exe
  const build = basename(dirname(dirname(full))).replace("chromium-", "");
  const root = join(dirname(dirname(dirname(full))), `chromium_headless_shell-${build}`);
  const folder = join(root, readdirSync(root).find((name) => name.startsWith("chrome-headless-shell")) ?? "");
  const program = readdirSync(folder).find((name) => /^chrome-headless-shell(\.exe)?$/.test(name)) ?? "";
  return join(folder, program);
}

// Key pages a visitor reaches without signing in: the shop, the home page, the console's sign-in, and the verify
// page's error state.
const HOME = "http://localhost:3000/";
const PAGES = [
  "http://localhost:3100/",
  HOME,
  "http://localhost:3000/console",
  "http://localhost:3000/v/vs_01M51KF05CE4GSBH7F0G43G01V",
];

test("key pages score at least 90 in Lighthouse, and the private ones stay out of search engines", () => {
  test.setTimeout(300_000);
  const args = [
    LHCI,
    "autorun",
    "--config=lighthouserc.json",
    `--collect.chromePath=${headlessShell()}`,
    ...PAGES.map((url) => `--collect.url=${url}`),
  ];
  // On Linux (GitHub's runners) Chrome's own sandbox can't start — Ubuntu 24.04 forbids the namespaces it needs — and
  // Lighthouse then waits for a browser that never comes. Playwright launches its browsers without that sandbox on
  // Linux for the same reason; Lighthouse's launcher is told to do the same. The pages are our own, on this machine.
  if (process.platform === "linux") {
    args.push("--collect.settings.chromeFlags=--headless --no-first-run --no-sandbox");
  }
  // Throws, failing the test, if a page misses an assertion in lighthouserc.json; the reports land in test-results.
  // The output is caught and, on failure, put in the error itself: CI shows a failing test's message to anyone, but
  // its full log only to people signed in to GitHub.
  try {
    execFileSync(process.execPath, args, { encoding: "utf8", stdio: "pipe" });
  } catch (error) {
    // No reports at all: Lighthouse failed before scoring (starting Chrome, loading a page). Show the end of its own
    // output instead.
    if (!existsSync("test-results/lighthouse/manifest.json")) {
      const { stdout = "", stderr = "" } = error as { stdout?: string; stderr?: string };
      const tail = `${stdout}\n${stderr}`.trim().split("\n").slice(-30).join("\n");
      throw new Error(`Lighthouse failed before scoring any page:\n${tail}`);
    }
    // Each page's scores, from the saved list of reports: enough to see which page fell short, and where.
    const saved: Array<{ url: string; summary: Record<string, number> }> = JSON.parse(
      readFileSync("test-results/lighthouse/manifest.json", "utf8"),
    );
    const scores = saved.map(({ url, summary }) => {
      const each = Object.entries(summary).map(([name, score]) => `${name} ${Math.round(score * 100)}`);
      return `${url}: ${each.join(", ")}`;
    });
    throw new Error(`a page scored under its minimum in lighthouserc.json:\n${scores.join("\n")}`);
  }

  // The console and the verify page are private: their search score can't reach 90, because they ask search engines
  // not to index them (layout.tsx). So the test checks the opposite — that they still ask. The home page asks to be
  // found, and its search score is held to 90 like the shop's (lighthouserc.json).
  const reports: Array<{ url: string; jsonPath: string }> = JSON.parse(
    readFileSync("test-results/lighthouse/manifest.json", "utf8"),
  );
  for (const { url, jsonPath } of reports.filter(
    (r) => r.url.startsWith("http://localhost:3000/") && r.url !== HOME,
  )) {
    const report = JSON.parse(readFileSync(jsonPath, "utf8"));
    expect(report.audits["is-crawlable"].score, `${url} must stay out of search engines`).toBe(0);
  }
});
