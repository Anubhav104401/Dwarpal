import { createHmac } from "node:crypto";

import { expect, type Page, test } from "@playwright/test";

import { violations } from "./axe.js";

const CONSOLE = "http://localhost:3000/console";
const API = "http://localhost:8000";

/** What an authenticator app does (RFC 6238): the 6-digit code for the 30-second step containing `at`. */
function oneTimeCode(secret: string, at: number): string {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const bits = [...secret.replace(/\s/g, "")]
    .map((c) => alphabet.indexOf(c).toString(2).padStart(5, "0"))
    .join("");
  const key = Buffer.from(bits.match(/.{8}/g)?.map((byte) => Number.parseInt(byte, 2)) ?? []);
  const step = Buffer.alloc(8);
  step.writeBigUInt64BE(BigInt(Math.floor(at / 30_000)));
  const mac = createHmac("sha1", key).update(step).digest();
  const offset = (mac.at(-1) ?? 0) & 0x0f;
  return String((mac.readUInt32BE(offset) & 0x7fffffff) % 1_000_000).padStart(6, "0");
}

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
  // Searching for an outcome nothing has yet finds nothing; "Any" finds it again.
  await page.getByLabel("Outcome").selectOption("pass");
  await sessions.getByRole("button", { name: "Search" }).click();
  await expect(sessions).toContainText("No sessions match.");
  await page.getByLabel("Outcome").selectOption("");
  await sessions.getByRole("button", { name: "Search" }).click();
  await expect(sessions).toContainText("created");
  await sessions.getByRole("button", { name: "Trace" }).click();
  await expect(page.getByRole("region", { name: "Decision trace" })).toContainText("No attempts.");

  // An owner adds a policy version on one of the model's lines; it is listed at once. The stand-in model the tests
  // use was never measured, so the editor offers no projection.
  await expect(page.getByLabel("Age line")).toHaveValue("18@0.02");
  await expect(page.getByRole("region", { name: "What the 18+ line means for adults" })).toContainText(
    "Not measured",
  );
  await page.getByLabel("New version of policy").fill("shop_18");
  // It accepts Age Passes (Phase 9): the website opts in, and the list says so.
  await page.getByLabel("Accept Age Passes").check();
  await page.getByRole("button", { name: "Add version" }).click();
  await expect(page.getByRole("region", { name: "Policies" })).toContainText("shop_18@1");
  await expect(page.getByRole("row", { name: /shop_18@1/ })).toContainText("accepted");

  // A webhook endpoint: its secret is shown once, and a test event waits to be delivered.
  await page.getByLabel("Endpoint URL").fill("http://localhost:3100/dwarpal-events");
  await page.getByRole("button", { name: "Add endpoint" }).click();
  await expect(page.getByTestId("new-secret")).toHaveText(/^whsec_/);
  await page.getByRole("button", { name: "Send test" }).click();
  await expect(page.getByRole("table", { name: "Recent deliveries" })).toContainText("pending");
  // Switched off, it is marked so; switched on again, the mark goes.
  await page.getByRole("button", { name: "Switch off" }).click();
  const webhooks = page.getByRole("region", { name: "Webhooks" });
  await expect(webhooks.getByText("Off", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Switch on" }).click();
  await expect(webhooks.getByText("Off", { exact: true })).toHaveCount(0);
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

test("a member turns on one-time codes, and signing in then asks for one", async ({ page }) => {
  const email = `careful-${Date.now()}@shop.example`;
  const password = "another long and unguessable test passphrase";
  await page.goto(CONSOLE);
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByLabel("Organisation name").fill("Careful Ltd");
  await page.getByRole("button", { name: "Create account" }).click();

  await page.getByRole("link", { name: "Security" }).click();
  await page.getByRole("button", { name: "Set up one-time codes" }).click();
  await expect(page.getByRole("img", { name: /QR code/ })).toBeVisible();
  const secret = (await page.getByTestId("totp-secret").textContent()) ?? "";
  await page.getByLabel("2. Enter the code it shows").fill(oneTimeCode(secret, Date.now()));
  await page.getByRole("button", { name: "Turn on" }).click();
  await expect(page.getByRole("region", { name: "One-time codes" })).toContainText("On.");
  const recovery = (
    (await page.getByTestId("recovery-codes").locator("li").first().textContent()) ?? ""
  ).trim();
  expect(recovery).toMatch(/^[a-z2-7]{5}-[a-z2-7]{5}$/);

  // Sign out and in again: the password alone is not enough. A code is single-use, so use the next step's.
  await page.getByRole("link", { name: "All organisations" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page
    .getByLabel("6-digit code from your authenticator app")
    .fill(oneTimeCode(secret, Date.now() + 30_000));
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();

  // A lost phone: sign in again with a recovery code instead, which is then used up.
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByLabel("6-digit code from your authenticator app").fill(recovery);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();
  await page.getByRole("link", { name: "Security" }).click();
  await expect(page.getByRole("region", { name: "One-time codes" })).toContainText("Recovery codes left: 9");

  // Turning codes off needs the password and a current code. Each code works once, and the next one was used to sign
  // in, so wait for the clock's next 30-second step — as a person would wait for a new code — and use the one after.
  await page.waitForTimeout(30_000 - (Date.now() % 30_000) + 200);
  await page.getByLabel("Your password").fill(password);
  await page.getByLabel("Code from your app").fill(oneTimeCode(secret, Date.now() + 30_000));
  await page.getByRole("button", { name: "Turn off" }).click();
  await expect(page.getByRole("button", { name: "Set up one-time codes" })).toBeVisible();
});

/** Create an account in this browser, with its own organisation. */
async function signUp(page: Page, email: string, organisation: string): Promise<void> {
  await page.goto(CONSOLE);
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill("a long and unguessable test passphrase");
  await page.getByLabel("Organisation name").fill(organisation);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();
}

test("the model page names the model the API is deciding with, and its line for each age", async ({
  page,
}) => {
  const configuration = await (await fetch(`${API}/.well-known/dwarpal-configuration`)).json();
  await signUp(page, `model-${Date.now()}@shop.example`, "Model Ltd");
  await page.getByRole("link", { name: "Age model" }).click();

  await expect(page.getByRole("heading", { name: "The age model" })).toBeVisible();
  await expect(page.getByText(configuration.age_model, { exact: true })).toBeVisible();
  const lines = page.getByRole("region", { name: "Its lines for each age" });
  for (const age of ["13+", "16+", "18+", "21+"])
    await expect(lines.getByRole("cell", { name: age })).toBeVisible();
});

test("the command palette finds a project by name and goes there from the keyboard", async ({ page }) => {
  await signUp(page, `palette-${Date.now()}@shop.example`, "Palette Ltd");
  const search = page.getByRole("searchbox", { name: "Search the console" });
  // The shortcut works once the page's script has started, which can trail the first paint by a moment.
  await expect(async () => {
    await page.keyboard.press("ControlOrMeta+k");
    await expect(search).toBeFocused({ timeout: 1_000 });
  }).toPass();

  await search.fill("palette default");
  await expect(page.getByRole("list", { name: "Results" }).getByRole("link")).toHaveText([/Default project/]);
  await search.press("ArrowDown");
  await expect(page.getByRole("link", { name: /Default project/ })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Webhooks" })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Go to" })).toBeHidden();
});

test("an owner adds a member, changes their role, and removes them", async ({ page, browser }) => {
  const owner = `team-owner-${Date.now()}@shop.example`;
  const colleague = `colleague-${Date.now()}@shop.example`;
  const theirs = await browser.newContext(); // the colleague's own browser, with their own session
  await signUp(await theirs.newPage(), colleague, "Their Ltd");
  await theirs.close();
  await signUp(page, owner, "Team Ltd");
  await page.getByRole("link", { name: /Team Ltd/ }).click();
  const members = page.getByRole("region", { name: "Members" });

  await page.getByLabel("Add by e-mail").fill(colleague);
  await page.getByLabel("Role", { exact: true }).selectOption("analyst");
  await members.getByRole("button", { name: "Add", exact: true }).click();
  const role = page.getByLabel(`Role of ${colleague}`);
  await expect(role).toHaveValue("analyst");

  await role.selectOption("developer");
  await expect(role).toHaveValue("developer");
  await page.reload(); // the change was saved, not just shown
  await expect(page.getByLabel(`Role of ${colleague}`)).toHaveValue("developer");

  await page.getByRole("button", { name: `Remove ${colleague}` }).click();
  await expect(members).not.toContainText(colleague);
});

test("an owner makes a project for their website, gives it a key, stops the key, and renames it", async ({
  page,
  request,
}, info) => {
  await signUp(page, `projects-${Date.now()}@shop.example`, "Projects Ltd");
  await page.getByRole("link", { name: /Projects Ltd/ }).click();

  // Decisions D28, D29: a project with its website's origins, written the standard way.
  await page.getByText("New project").click();
  await page.getByLabel("Name", { exact: true }).fill("Cellar shop");
  await page.getByLabel("Allowed origins, one per line").fill("HTTPS://Shop.Example/\nhttp://localhost:3100");
  await page.getByRole("button", { name: "Create project" }).click();
  const projects = page.getByRole("region", { name: "Projects and API keys" });
  await expect(projects).toContainText("https://shop.example · http://localhost:3100");

  // A key for it; a website using the key may return checks only to those origins.
  await page.getByLabel("Project", { exact: true }).selectOption({ label: "Cellar shop" });
  await page.getByRole("button", { name: "Create key" }).click();
  const key = (await page.getByTestId("new-key").textContent()) ?? "";
  const session = (returnUrl: string) =>
    request.post(`${API}/v1/verification-sessions`, {
      headers: { Authorization: `Bearer ${key}` },
      data: { policy: "uk_osa_18", return_url: returnUrl },
    });
  expect((await session("http://localhost:3100/age-check/complete")).status()).toBe(201);
  expect((await session("https://elsewhere.example/done")).status()).toBe(422);

  // D30: the project's page lists the key without its secret, and stops it at once.
  await page.getByRole("link", { name: "Cellar shop" }).click();
  const keys = page.getByRole("region", { name: "API keys" });
  await expect(keys).not.toContainText(key);
  page.once("dialog", (dialog) => dialog.accept());
  await keys.getByRole("button", { name: /^Stop key/ }).click();
  await expect(keys.getByText("Stopped")).toBeVisible();
  expect((await session("http://localhost:3100/age-check/complete")).status()).toBe(401);

  // Renamed in its settings; the heading follows.
  const settings = page.getByRole("region", { name: "Settings" });
  await settings.getByLabel("Name").fill("Amber Cellars shop");
  await settings.getByRole("button", { name: "Save" }).click();
  await expect(settings.getByText("Saved.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Amber Cellars shop" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("project.png"), fullPage: true, animations: "disabled" });
});

test("an owner invites someone without an account, who joins on signing up", async ({ page, browser }) => {
  const newcomer = `newcomer-${Date.now()}@shop.example`;
  await signUp(page, `inviter-${Date.now()}@shop.example`, "Inviting Ltd");
  await page.getByRole("link", { name: /Inviting Ltd/ }).click();
  const members = page.getByRole("region", { name: "Members" });

  // Decision D44: no account yet, so an invitation waits (no e-mail is sent).
  await page.getByLabel("Add by e-mail").fill(newcomer);
  await page.getByLabel("Role", { exact: true }).selectOption("developer");
  await members.getByRole("button", { name: "Add", exact: true }).click();
  await expect(members.getByRole("status")).toContainText("has no account yet, so they are invited");
  await expect(members).toContainText("Invited, not signed up yet");

  const theirs = await browser.newContext();
  const theirPage = await theirs.newPage();
  await signUp(theirPage, newcomer, "Newcomer Ltd");
  await expect(theirPage.getByRole("link", { name: /Inviting Ltd/ })).toBeVisible(); // they joined on signing up
  await theirs.close();

  await page.reload();
  await expect(page.getByLabel(`Role of ${newcomer}`)).toHaveValue("developer");
  await expect(members).not.toContainText("Invited, not signed up yet");
});

test("a new password signs every other browser out, and an account can be deleted", async ({
  page,
  browser,
}) => {
  const email = `account-${Date.now()}@shop.example`;
  const password = "a long and unguessable test passphrase";
  const changed = "a different and equally long test passphrase";
  await signUp(page, email, "Account Ltd");
  const other = await browser.newContext();
  const otherPage = await other.newPage();
  await otherPage.goto(CONSOLE);
  await otherPage.getByLabel("E-mail address").fill(email);
  await otherPage.getByLabel("Password").fill(password);
  await otherPage.getByRole("button", { name: "Sign in" }).click();
  await expect(otherPage.getByRole("heading", { name: "Your organisations" })).toBeVisible();

  // Decision D31: the old password, a new one; this browser stays signed in, the other is signed out.
  await page.goto(`${CONSOLE}/account`);
  const section = page.getByRole("region", { name: "Password" });
  await section.getByLabel("Current password").fill(password);
  await section.getByLabel("New password (at least 12 characters)").fill(changed);
  await section.getByRole("button", { name: "Change password" }).click();
  await expect(section.getByRole("status")).toHaveText(
    "Password changed. Every other browser has been signed out.",
  );
  await otherPage.reload();
  await expect(otherPage.getByRole("button", { name: "Sign in" })).toBeVisible();
  await other.close();

  // Decision D32: deleting the account needs the password and a tick; then it is gone, and signed out.
  const deletion = page.getByRole("region", { name: "Delete your account" });
  await deletion.getByLabel("Password, to confirm it's you").fill(changed);
  await deletion.getByLabel("I understand this can't be undone.").check();
  await deletion.getByRole("button", { name: "Delete my account" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("E-mail address").fill(email);
  await page.getByLabel("Password").fill(changed);
  await page.getByRole("button", { name: "Sign in" }).click();
  // (By its text: after a navigation, Next.js's own route announcer is an alert too.)
  await expect(page.getByText("That e-mail address or password is wrong.")).toBeVisible();
});

test("a live check opens on the document check while no age model is certified (D24)", async ({
  page,
  request,
}) => {
  await signUp(page, `live-${Date.now()}@shop.example`, "Live Ltd");
  await page.getByRole("link", { name: /Live Ltd/ }).click();
  await page.getByLabel(/Live key/).check();
  await page.getByRole("button", { name: "Create key" }).click();
  const key = (await page.getByTestId("new-key").textContent()) ?? "";
  expect(key).toMatch(/^dk_live_/);

  const created = await request.post(`${API}/v1/verification-sessions`, {
    headers: { Authorization: `Bearer ${key}` },
    data: { policy: "uk_osa_18" },
  });
  expect(created.status()).toBe(201);
  const { id, client_secret: secret } = await created.json();
  await page.goto(`http://localhost:3000/v/${id}#cs=${secret}`);
  await expect(page.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  await expect(page.getByText("checks your age with an ID document")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start the camera" })).toHaveCount(0);
  await page.getByRole("button", { name: "Use a passport or ID card" }).click();
  await expect(page.getByRole("heading", { name: "Confirm your age with an ID document" })).toBeVisible();
});

test("every page load gets its own script nonce, and inline scripts aren't allowed", async ({ request }) => {
  const policies = [];
  for (const _ of [1, 2]) {
    const answer = await request.get(CONSOLE);
    policies.push(answer.headers()["content-security-policy"] ?? "");
  }
  const scripts = policies.map((p) => p.split("; ").find((part) => part.startsWith("script-src")) ?? "");
  const nonces = scripts.map((s) => /'nonce-([^']+)'/.exec(s)?.[1]);
  expect(nonces[0]).toBeTruthy();
  expect(nonces[0]).not.toBe(nonces[1]); // a fresh nonce each time
  expect(scripts[0]).not.toContain("'unsafe-inline'");
});

test("a member adds a passkey, then signs in with it alone", async ({ page, browserName }) => {
  // Chromium's virtual authenticator stands in for a phone or security key: a real key pair, made in the browser.
  test.skip(browserName !== "chromium", "the virtual authenticator is a Chromium DevTools feature");
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("WebAuthn.enable");
  await cdp.send("WebAuthn.addVirtualAuthenticator", {
    options: {
      protocol: "ctap2",
      transport: "internal",
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true,
    },
  });
  await signUp(page, `passkey-${Date.now()}@shop.example`, "Passkey Ltd");

  await page.getByRole("link", { name: "Security" }).click();
  const passkeys = page.getByRole("region", { name: "Passkeys" });
  await passkeys.getByLabel("A name for it").fill("Test laptop");
  await passkeys.getByLabel("Password, to confirm it's you").fill("a long and unguessable test passphrase");
  await passkeys.getByRole("button", { name: "Add a passkey" }).click();
  await expect(page.getByTestId("passkey-list")).toContainText("Test laptop");

  // Sign out, then in with the passkey: no e-mail address, no password.
  await page.getByRole("link", { name: "All organisations" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByRole("button", { name: "Use a passkey instead" }).click();
  await expect(page.getByRole("heading", { name: "Your organisations" })).toBeVisible();
  await page.getByRole("link", { name: "Security" }).click();
  await expect(page.getByTestId("passkey-list")).toContainText("last used");
});
