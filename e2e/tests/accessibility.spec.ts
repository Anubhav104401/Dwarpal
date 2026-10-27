import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

const SHOP = "http://localhost:3100";
const CONSOLE = "http://localhost:3000/console";
// The rules of WCAG 2.2 at levels A and AA, as axe-core tags them (earlier versions' rules included).
const STANDARDS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** Every accessibility rule the page breaks, as "rule — what it means — where"; empty when it breaks none. */
async function violations(page: Page): Promise<string[]> {
  // Let one-off animations (a card fading in) finish: colours measured mid-fade are blends, not the page's colours.
  // Endless ones (a spinner) never finish, so they are left out.
  await page.evaluate(() =>
    Promise.all(
      document
        .getAnimations()
        .filter((a) => a.effect?.getTiming().iterations !== Number.POSITIVE_INFINITY)
        .map((a) => a.finished),
    ),
  );
  const results = await new AxeBuilder({ page }).withTags(STANDARDS).analyze();
  return results.violations.map(
    (v) => `${v.id} — ${v.help} — ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`,
  );
}

test("the shop, and the verify page before the camera, break no accessibility rule", async ({ page }) => {
  await page.goto(SHOP);
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeVisible();
  expect(await violations(page)).toEqual([]);

  await page.getByRole("button", { name: "Verify my age to enter" }).click();
  await expect(page.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
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
});
