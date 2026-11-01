import { expect, test } from "@playwright/test";

import { violations } from "./axe.js";

test("the home page shows the running model's lines, and leads to the demo shop and the console", async ({
  page,
}) => {
  await page.goto("http://localhost:3000/");
  const accuracy = page.getByRole("region", { name: "Accuracy, measured" });
  for (const age of ["13+", "16+", "18+", "21+"]) {
    await expect(accuracy.getByRole("rowheader", { name: age })).toBeVisible();
  }
  // The tests' API runs the stand-in model, whose lines were never measured: the table says so rather than guess.
  await expect(accuracy.getByRole("cell", { name: "not measured" }).first()).toBeVisible();
  await expect(accuracy).toContainText("decides test checks only");

  const shop = page.getByRole("link", { name: "Try it on the demo shop" });
  await expect(shop).toHaveAttribute("href", "http://localhost:3100");
  await page.getByRole("link", { name: "Console", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("the hero's face turns 3D where the browser can draw it, and stays still for anyone who asks for less motion", async ({
  page,
  browser,
}) => {
  await page.goto("http://localhost:3000/");
  const webgl = await page.evaluate(() => document.createElement("canvas").getContext("webgl2") !== null);
  test.skip(!webgl, "this browser can't draw WebGL here");
  // Once the page is idle, the 3D face takes the still face's place: the doorway's points are gone.
  await expect(page.locator("canvas")).toBeVisible({ timeout: 10_000 });
  await expect(page.locator('svg[viewBox="0 0 240 280"] circle')).toHaveCount(0);

  const calm = await browser.newPage({ reducedMotion: "reduce" });
  await calm.goto("http://localhost:3000/");
  await calm.waitForTimeout(3_000);
  await expect(calm.locator("canvas")).toBeHidden();
  await expect(calm.locator('svg[viewBox="0 0 240 280"] circle')).toHaveCount(168);
  await calm.close();
});

test("the home page speaks Hindi to anyone who chooses it, and remembers the choice", async ({ page }) => {
  await page.goto("http://localhost:3000/");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.getByRole("button", { name: "हिन्दी" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("देखो। तय करो। भूल जाओ।");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
  await expect(page).toHaveTitle("द्वारपाल · निजी उम्र जाँच");
  for (const question of await page.locator("details").all()) {
    await question.evaluate((element) => element.setAttribute("open", ""));
  }
  expect(await violations(page)).toEqual([]);

  // Remembered on the next visit; and English is one press away.
  await page.reload();
  await expect(page.getByRole("button", { name: "हिन्दी" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "English" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Look. Decide. Forget.");
});

test("a browser that asks for Hindi gets it without choosing, and the console stays English", async ({
  browser,
}) => {
  const context = await browser.newContext({ locale: "hi-IN" });
  const page = await context.newPage();
  await page.goto("http://localhost:3000/");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
  await expect(page.getByRole("heading", { name: "यह कैसे काम करता है" })).toBeVisible();
  // The console is written in English only, and says so for screen readers.
  await page.goto("http://localhost:3000/console");
  await expect(page.locator("div[lang=en]").first()).toContainText("Sign in");
  await context.close();
});
