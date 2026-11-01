import { fileURLToPath } from "node:url";

import { type APIRequestContext, expect, test } from "@playwright/test";

import { violations } from "./axe.js";

const SHOP = "http://localhost:3100";
const VERIFY = "http://localhost:3000";
const API = "http://127.0.0.1:8000";
const SPECIMEN = fileURLToPath(new URL("../.cache/specimen-passport.jpg", import.meta.url));

test("an adult passes the age check in a modal over the shop, and is let into the cellar", async ({
  page,
}, info) => {
  await page.goto(SHOP);
  await page.getByRole("button", { name: "Verify my age to enter" }).click();

  // The check opens over the shop, in a frame (decision D16): the shop's page stays where it is.
  const modal = page.getByRole("dialog", { name: "Age check" });
  const check = page.frameLocator('iframe[title="Age check"]');
  await expect(check.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  expect(page.url()).toBe(`${SHOP}/`);
  await expect(modal.locator("iframe")).toHaveAttribute(
    "src",
    /^http:\/\/localhost:3000\/v\/vs_[0-9A-Z]{26}#cs=/,
  );
  // Inside the frame, the verify page has wiped the secret from its own address.
  const framed = page.frames().find((frame) => frame.url().startsWith(`${VERIFY}/v/`));
  expect(framed?.url()).toMatch(/^http:\/\/localhost:3000\/v\/vs_[0-9A-Z]{26}$/);
  await page.screenshot({ path: info.outputPath("1-intro.png"), animations: "disabled" });

  await check.getByRole("button", { name: "Start the camera" }).click();
  // Enabled once the guidance is satisfied, or after its grace period: it advises, the server decides.
  await expect(check.getByRole("button", { name: "Start", exact: true })).toBeEnabled({ timeout: 15_000 });
  await page.screenshot({ path: info.outputPath("2-camera.png"), animations: "disabled" });
  await check.getByRole("button", { name: "Start", exact: true }).click();
  // The screen colours, then each pose: the still portrait never turns, so each pose waits out its 5 seconds.
  await expect(check.getByText("Keep looking at the screen.").first()).toBeVisible();
  await page.screenshot({ path: info.outputPath("3-light.png"), animations: "disabled" });
  await expect(check.getByText(/^(Turn your head|Lift your chin)/).first()).toBeVisible({
    timeout: 10_000,
  });
  await page.screenshot({ path: info.outputPath("4-pose.png"), animations: "disabled" });
  await expect(check.getByRole("heading", { name: "You're all set" })).toBeVisible({ timeout: 45_000 });
  await page.screenshot({ path: info.outputPath("5-passed.png"), animations: "disabled" });

  // "Continue" tells the shop's page, which goes to the shop's return address; the shop's server checks the result.
  await check.getByRole("button", { name: /^Continue to / }).click();
  await expect(modal).toHaveCount(0);
  await expect(page).toHaveURL(`${SHOP}/cellar`);
  await expect(page.getByRole("status")).toContainText("Age verified");
  await page.screenshot({ path: info.outputPath("6-cellar.png"), fullPage: true, animations: "disabled" });

  // Leaving forgets the pass: the cellar is closed again until a new check.
  await page.getByRole("button", { name: "Leave the cellar" }).click();
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeVisible();
  await page.goto(`${SHOP}/cellar`);
  await expect(page).toHaveURL(`${SHOP}/`);
});

test("the cellar stays closed to anyone without a pass", async ({ page }) => {
  await page.goto(`${SHOP}/cellar`);
  await expect(page).toHaveURL(`${SHOP}/`);
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeVisible();
});

test("a verify link without its secret explains what to do, in the person's language", async ({
  page,
  browser,
}) => {
  await page.goto(`${VERIFY}/v/vs_01M51KF05CE4GSBH7F0G43G01V`);
  await expect(page.getByRole("heading", { name: "This link doesn't work" })).toBeVisible();
  const hindi = await browser.newContext({ locale: "hi-IN" });
  const other = await hindi.newPage();
  await other.goto(`${VERIFY}/v/vs_01M51KF05CE4GSBH7F0G43G01V`);
  await expect(other.getByRole("heading", { name: "यह लिंक काम नहीं करता" })).toBeVisible();
  await hindi.close();
});

test("a return link only works in the browser that started the check", async ({ page }) => {
  await page.goto(`${SHOP}/age-check/complete?session_id=vs_01M51KF05CE4GSBH7F0G43G01V`);
  await expect(page).toHaveURL(`${SHOP}/refused?reason=other_browser`);
  await expect(
    page.getByRole("heading", { name: "Please finish the check where you started it" }),
  ).toBeVisible();
});

test("the modal closes, and the shop's page is just as it was", async ({ page }) => {
  await page.goto(SHOP);
  await page.getByRole("button", { name: "Verify my age to enter" }).click();
  const check = page.frameLocator('iframe[title="Age check"]');
  await expect(check.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  await page.getByRole("button", { name: "Close the age check" }).click();
  await expect(page.getByRole("dialog", { name: "Age check" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeFocused();
});

test("no other website may frame a verify page", async ({ page }) => {
  const answer = await page.request.get(`${VERIFY}/v/vs_01M51KF05CE4GSBH7F0G43G01V`);
  expect(answer.headers()["content-security-policy"]).toContain("frame-ancestors 'none'");
});

/** A session the face check couldn't decide: three attempts whose frames can't even be read, so it steps up. */
async function steppedUp(request: APIRequestContext): Promise<{ id: string; secret: string }> {
  const created = await request.post(`${API}/v1/verification-sessions`, {
    headers: { Authorization: `Bearer ${process.env.E2E_API_KEY}` },
    data: { policy: "uk_osa_18" },
  });
  const { id, client_secret: secret } = await created.json();
  const started = await request.post(`${API}/v1/flow/sessions/${id}/start`, {
    data: { client_secret: secret },
  });
  const flow = { Authorization: `Bearer ${(await started.json()).flow_token}` };
  let outcome = "";
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const challenge = await (
      await request.post(`${API}/v1/flow/sessions/${id}/challenge`, { headers: flow })
    ).json();
    const frames = Array.from({ length: 3 }, (_, index) => ({ index, t_ms: index * 120, phase: "baseline" }));
    const multipart: Record<string, string | { name: string; mimeType: string; buffer: Buffer }> = {
      challenge_id: challenge.challenge_id,
      meta: JSON.stringify({ frames }),
    };
    for (const frame of frames) {
      multipart[`frame_${frame.index}`] = {
        name: "f.jpg",
        mimeType: "image/jpeg",
        buffer: Buffer.from("not a picture"),
      };
    }
    const answer = await request.post(`${API}/v1/flow/sessions/${id}/face-attempts`, {
      headers: flow,
      multipart,
    });
    outcome = (await answer.json()).outcome;
  }
  expect(outcome).toBe("step_up");
  return { id, secret };
}

test("a person the face check can't decide confirms their age with a passport and a selfie", async ({
  page,
  request,
}, info) => {
  const { id, secret } = await steppedUp(request);
  await page.goto(`${VERIFY}/v/${id}#cs=${secret}`);
  await expect(page.getByRole("heading", { name: "We need a stronger check" })).toBeVisible();
  await page.getByRole("button", { name: "Use a passport or ID card" }).click();

  // What happens, said before anything is chosen; then the photo of the passport's page.
  await expect(page.getByRole("heading", { name: "Confirm your age with an ID document" })).toBeVisible();
  await expect(page.getByText("Your name and document number are never kept")).toBeVisible();
  expect(await violations(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("1-document.png"), animations: "disabled" });
  await page.getByLabel("Take or choose a photo of your document").setInputFiles(SPECIMEN);

  // Then a selfie, with the same challenge as a face check: the fake camera plays the passport's face.
  await expect(page.getByText("Now a short selfie")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start", exact: true })).toBeEnabled({ timeout: 15_000 });
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: info.outputPath("2-passed.png"), animations: "disabled" });

  // The website's view: passed, and the token says how.
  const result = await request.get(`${API}/v1/verification-sessions/${id}`, {
    headers: { Authorization: `Bearer ${process.env.E2E_API_KEY}` },
  });
  const session = await result.json();
  expect([session.status, session.outcome]).toEqual(["completed", "pass"]);
  const claims = JSON.parse(Buffer.from(session.age_token.split(".")[1], "base64url").toString());
  expect(claims.methods).toEqual(["face_estimation", "document_mrz", "face_match"]);
});
