import { describe, expect, it } from "vitest";

import { shopConfig } from "./config";

const SETTINGS: NodeJS.ProcessEnv = {
  NODE_ENV: "test",
  DWARPAL_API_KEY: "dk_test_example",
  DWARPAL_PROJECT_ID: "prj_01M736PBVVFF5SJ439KP2QVVKQ",
  SHOP_SECRET: "s".repeat(32),
};

describe("the shop's settings", () => {
  it("are read from the environment", () => {
    expect(shopConfig(SETTINGS).projectId).toBe("prj_01M736PBVVFF5SJ439KP2QVVKQ");
  });

  it("refuse a project ID in the database's UUID form", () => {
    const env = { ...SETTINGS, DWARPAL_PROJECT_ID: "01a1c66b-2f7b-7bcb-9910-699d857dee77" };
    expect(() => shopConfig(env)).toThrow("DWARPAL_PROJECT_ID (the console's prj_… form)");
  });

  it("refuse missing settings, naming each", () => {
    expect(() => shopConfig({ NODE_ENV: "test" })).toThrow("DWARPAL_API_KEY, DWARPAL_PROJECT_ID");
  });
});
