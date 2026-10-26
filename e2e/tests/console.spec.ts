import { expect, test } from "@playwright/test";

const CONSOLE = "http://localhost:3000/console";

test("a new customer signs up, creates an API key, and sees it in an intact audit log", async ({
  page,
}, info) => {
  const email = `owner-${Date.now()}@shop.example`;
  await page.goto(CONSOLE);
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill("a long and unguessable test passphrase");
  await page.getByLabel("Organisation name").fill("Amber Cellars Ltd");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();
  await page.getByRole("link", { name: /Amber Cellars Ltd/ }).click();
  await expect(page.getByRole("heading", { name: "Amber Cellars Ltd" })).toBeVisible();
  await expect(page.getByText("Your role: owner")).toBeVisible();
  await expect(page.getByRole("region", { name: "Members" })).toContainText(email);

  await page.getByRole("button", { name: "Create key" }).click();
  await expect(page.getByTestId("new-key")).toHaveText(/^dk_test_/);
  await expect(page.getByText("Chain intact")).toBeVisible();
  const audit = page.getByRole("region", { name: "Audit log" });
  await expect(audit).toContainText("api_key.created");
  await expect(audit).toContainText("organisation.created");
  await page.screenshot({ path: info.outputPath("console.png"), fullPage: true, animations: "disabled" });

  // The key is shown once: after a reload, only the facts remain.
  await page.reload();
  await expect(page.getByTestId("new-key")).toHaveCount(0);
});

test("the console refuses a wrong password without saying whether the account exists", async ({ page }) => {
  await page.goto(CONSOLE);
  await page.getByLabel("E-mail address").fill(`nobody-${Date.now()}@shop.example`);
  await page.getByLabel("Password").fill("not the right password");
  await page.getByRole("button", { name: "Sign in" }).click();
  // Next.js keeps its own, empty role="alert" region for route changes; this is the one with words in it.
  const alert = page.getByRole("alert").filter({ hasText: /\S/ });
  await expect(alert).toHaveText("That e-mail address or password is wrong.");
});
