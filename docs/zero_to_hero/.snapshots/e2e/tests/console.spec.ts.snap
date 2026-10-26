import { expect, test } from "@playwright/test";

const CONSOLE = "http://localhost:3000/console";
const API = "http://localhost:8000";

test("a new customer signs up, creates an API key, and sees it in an intact audit log", async ({
  page,
  request,
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
  const key = (await page.getByTestId("new-key").textContent()) ?? "";
  await page.reload();
  await expect(page.getByTestId("new-key")).toHaveCount(0);

  // A website uses the key; the session appears on the project's page, with its (empty) decision trace.
  const created = await request.post(`${API}/v1/verification-sessions`, {
    headers: { Authorization: `Bearer ${key}` },
    data: { policy: "uk_osa_18" },
  });
  expect(created.status()).toBe(201);
  await page.getByRole("link", { name: "Default project" }).click();
  await expect(page.getByRole("heading", { name: "Default project" })).toBeVisible();
  const sessions = page.getByRole("region", { name: "Sessions" });
  await expect(sessions).toContainText("created");
  await sessions.getByRole("button", { name: "Trace" }).click();
  await expect(page.getByRole("region", { name: "Decision trace" })).toContainText("No attempts.");

  // An owner adds a policy version; it is listed at once.
  await page.getByLabel("New version of policy").fill("shop_18");
  await page.getByRole("button", { name: "Add version" }).click();
  await expect(page.getByRole("region", { name: "Policies" })).toContainText("shop_18@1");

  // A webhook endpoint: its secret is shown once, and a test event waits to be delivered.
  await page.getByLabel("Endpoint URL").fill("http://localhost:3100/dwarpal-events");
  await page.getByRole("button", { name: "Add endpoint" }).click();
  await expect(page.getByTestId("new-secret")).toHaveText(/^whsec_/);
  await page.getByRole("button", { name: "Send test" }).click();
  await expect(page.getByRole("table", { name: "Recent deliveries" })).toContainText("pending");
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
