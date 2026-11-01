import { expect, test } from "@playwright/test";

import { violations } from "./axe.js";

const SHOP = "http://localhost:3100";
const CONSOLE = "http://localhost:3000/console";

test("the shop, and the verify page before the camera, break no accessibility rule", async ({ page }) => {
  await page.goto(SHOP);
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  // The check opens in a modal over the shop (decision D16); axe looks inside its frame too.
  await page.getByRole("button", { name: "Verify my age to enter" }).click();
  const check = page.frameLocator('iframe[title="Age check"]');
  await expect(check.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
});

test("the console's pages break no accessibility rule", async ({ page }) => {
  await page.goto(CONSOLE);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("E-mail address").fill(`axe-${Date.now()}@shop.example`);
  await page.getByLabel("Password").fill("a long and unguessable test passphrase");
  await page.getByLabel("Organisation name").fill("Axe Ltd");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.getByRole("link", { name: /Axe Ltd/ }).click();
  await expect(page.getByRole("heading", { name: "Audit log" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.getByRole("link", { name: "Default project" }).click();
  await expect(page.getByRole("heading", { name: "Webhooks" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.goto(`${CONSOLE}/account`);
  await page.getByRole("button", { name: "Set up one-time codes" }).click();
  await expect(page.getByRole("img", { name: /QR code/ })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.goto(`${CONSOLE}/model`);
  await expect(page.getByRole("heading", { name: "The age model" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.getByRole("button", { name: /Go to/ }).click();
  await expect(page.getByRole("searchbox", { name: "Search the console" })).toBeFocused();
  expect(await violations(page)).toEqual([]);
});

test("the home page breaks no accessibility rule, in the light or the dark theme, with its questions open", async ({
  page,
}) => {
  for (const colorScheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme });
    await page.goto("http://localhost:3000/");
    await expect(page.getByRole("heading", { name: "Look. Decide. Forget." })).toBeVisible();
    for (const question of await page.locator("summary").all()) await question.click();
    expect(await violations(page), `${colorScheme} theme`).toEqual([]);
  }
});

test("the design system's specimen breaks no accessibility rule, in the light or the dark theme", async ({
  page,
}) => {
  for (const colorScheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme });
    await page.goto("http://localhost:3000/design");
    await expect(page.getByRole("heading", { name: "Design system" })).toBeVisible();
    expect(await violations(page), `${colorScheme} theme`).toEqual([]);
  }
});
