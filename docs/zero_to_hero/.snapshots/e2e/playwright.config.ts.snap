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
  ],
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
    ),
    server("pnpm --filter @dwarpal/web start", "http://localhost:3000"),
    server("pnpm --filter @dwarpal/demo-shop start", "http://localhost:3100", shopEnv),
  ],
});
