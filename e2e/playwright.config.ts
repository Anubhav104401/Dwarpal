import { execFileSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const FAKE_CAMERA = fileURLToPath(new URL("./.cache/fake-camera.y4m", import.meta.url));
const UV = process.env.UV ?? "uv";
const CI = process.env.CI !== undefined;

function run(command: string, args: string[]): string {
  return execFileSync(command, args, { cwd: ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
}

/** Done once, by the main Playwright process: databases, tables, a demo project with a fresh key, the fake camera. */
function prepare(): Record<string, string> {
  run("docker", ["compose", "-f", "infra/compose/compose.yaml", "up", "-d", "--wait"]);
  run(UV, ["run", "--package", "dwarpal-api", "python", "-m", "dwarpal_api.cli", "migrate"]);
  const seeded = run(UV, ["run", "--package", "dwarpal-api", "python", "-m", "dwarpal_api.cli", "seed-dev"]);
  const project = /project:\s+(prj_\S+)/.exec(seeded)?.[1];
  const key = /test key:\s+(dk_test_\S+)/.exec(seeded)?.[1];
  if (project === undefined || key === undefined) {
    throw new Error("seed-dev did not print a project and a key");
  }
  if (!existsSync(FAKE_CAMERA)) {
    run(UV, ["run", "python", "infra/scripts/make_fake_camera.py", FAKE_CAMERA]);
  }
  return {
    DWARPAL_PROJECT_ID: project,
    DWARPAL_API_KEY: key,
    SHOP_SECRET: randomBytes(32).toString("base64url"),
  };
}

const shopEnv = process.env.TEST_WORKER_INDEX === undefined ? prepare() : {};

// The browser engines to test: all three unless E2E_ENGINES names some ("chromium,webkit"), for a machine where one
// can't start. (Playwright's Firefox 157 fails to start on Windows 11 build 26200: see the Phase 5 report.)
const ENGINES = (process.env.E2E_ENGINES ?? "chromium,firefox,webkit").split(",");
const CAMERA_OR_LIGHTHOUSE = ["age-check.spec.ts", "lighthouse.spec.ts"];

const server = (command: string, url: string, env: Record<string, string> = {}) => ({
  command,
  url,
  env,
  cwd: ROOT,
  reuseExistingServer: !CI,
  timeout: 180_000,
  stdout: "ignore" as const,
  stderr: "pipe" as const,
});

export default defineConfig({
  testDir: "tests",
  timeout: 90_000,
  retries: CI ? 1 : 0,
  workers: 1,
  reporter: CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3100",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      testIgnore: "lighthouse.spec.ts",
      use: {
        ...devices["Desktop Chrome"],
        permissions: ["camera"],
        launchOptions: {
          args: [
            "--use-fake-ui-for-media-stream",
            // Hide the automation flag, as an attacker's browser would: the server never trusts the page's signals.
            "--disable-blink-features=AutomationControlled",
            "--use-fake-device-for-media-stream",
            `--use-file-for-fake-video-capture=${FAKE_CAMERA}`,
          ],
        },
      },
    },
    // Two more browser engines for everything without a camera. Only Chromium can play a video file as a camera,
    // so the age-check story stays there; the console, and the accessibility checks, run on all three.
    { name: "firefox", use: { ...devices["Desktop Firefox"] }, testIgnore: CAMERA_OR_LIGHTHOUSE },
    { name: "webkit", use: { ...devices["Desktop Safari"] }, testIgnore: CAMERA_OR_LIGHTHOUSE },
    // Lighthouse runs Chromium itself, once: it goes with the Chromium engine.
    { name: "lighthouse", testMatch: "lighthouse.spec.ts" },
  ].filter((project) => ENGINES.includes(project.name === "lighthouse" ? "chromium" : project.name)),
  webServer: [
    server(
      `${UV} run --package dwarpal-inference uvicorn dwarpal_inference.main:create_app --factory --port 8001`,
      "http://127.0.0.1:8001/readyz",
      // The fake camera plays a still portrait, which can't turn its head: liveness trusts the frames' labels here,
      // a test mode allowed only with the stand-in age model (§5.3).
      { DWARPAL_INFERENCE_STUB_AGE: "30", DWARPAL_INFERENCE_LIVENESS: "labels" },
    ),
    server(
      `${UV} run --package dwarpal-api uvicorn dwarpal_api.main:create_app --factory --port 8000 --log-config services/api/logging.json`,
      "http://127.0.0.1:8000/readyz",
      // The console test registers a webhook on the demo shop's address, which is local: allow it, here only. And
      // these servers speak plain HTTP, where WebKit drops a Secure cookie, so the console's session cookie is plain
      // here; the API's tests check the production cookie (__Host-, Secure), and production refuses to run without it.
      // Every engine signs in from this one computer, and the limiter remembers earlier runs (in Valkey), so the sign-in
      // limit per address gets room for them all and refills fast.
      {
        DWARPAL_WEBHOOK_ALLOW_PRIVATE: "true",
        DWARPAL_CONSOLE_COOKIE_SECURE: "false",
        DWARPAL_LOGIN_BURST: "100",
        DWARPAL_LOGIN_PER_MINUTE: "600",
      },
    ),
    // The home page links to the demo shop when it knows where the shop is.
    server("pnpm --filter @dwarpal/web start", "http://localhost:3000", {
      DWARPAL_DEMO_SHOP_URL: "http://localhost:3100",
    }),
    server("pnpm --filter @dwarpal/demo-shop start", "http://localhost:3100", shopEnv),
  ],
});
