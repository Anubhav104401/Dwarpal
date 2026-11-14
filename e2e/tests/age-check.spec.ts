import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { type APIRequestContext, expect, test } from "@playwright/test";

import { violations } from "./axe.js";

const SHOP = "http://localhost:3100";
const VERIFY = "http://localhost:3000";
const API = "http://127.0.0.1:8000";
const INFERENCE = "http://127.0.0.1:8001";
const SPECIMEN = fileURLToPath(new URL("../.cache/specimen-passport.jpg", import.meta.url));

/** What the inference service says, right now, about the specimen passport with its own face as the selfie: whether
 * it answers, how fast, and whether the OCR read the zone. "The checker is busy" can mean any of these. */
async function probeDocumentCheck(request: APIRequestContext): Promise<string> {
  const specimen = readFileSync(SPECIMEN);
  const started = Date.now();
  try {
    const response = await request.post(`${INFERENCE}/internal/v1/analyze/document`, {
      multipart: {
        meta: JSON.stringify({ frames: [{ index: 0, t_ms: 0 }] }),
        frame_0: { name: "frame_0.jpg", mimeType: "image/jpeg", buffer: specimen },
        document: { name: "document.jpg", mimeType: "image/jpeg", buffer: specimen },
      },
      timeout: 60_000,
    });
    const took = Date.now() - started;
    if (!response.ok()) {
      return `inference answered ${response.status()} after ${took} ms: ${(await response.text()).slice(0, 200)}`;
    }
    const body = await response.json();
    return (
      `inference answered after ${took} ms (its own time ${Math.round(body.duration_ms)} ms): ` +
      `zone ${body.zone.length} lines, problem ${body.zone_problem}, document faces ${body.document_faces}`
    );
  } catch (error) {
    return `inference didn't answer after ${Date.now() - started} ms: ${String(error).slice(0, 200)}`;
  }
}

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

test("a person the face check can't decide is offered Aadhaar first in a test check, and a passport too", async ({
  page,
  request,
}, info) => {
  // Reading the document and matching two faces runs on the processor alone on CI's machines: allow it time.
  test.setTimeout(180_000);
  const { id, secret } = await steppedUp(request);
  await page.goto(`${VERIFY}/v/${id}#cs=${secret}`);
  await expect(page.getByRole("heading", { name: "We need a stronger check" })).toBeVisible();
  await page.getByRole("button", { name: "Use my Aadhaar" }).click();

  // What happens, said before anything is chosen: Aadhaar's QR code first (Part 7), and the passport as the other way.
  await expect(page.getByRole("heading", { name: "Confirm your age with Aadhaar" })).toBeVisible();
  await expect(
    page.getByText("Your Aadhaar number, name and address are never read out or kept"),
  ).toBeVisible();
  await expect(
    page.getByText("Using Aadhaar is your choice. A passport or ID card works just as well"),
  ).toBeVisible();
  expect(await violations(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("1-document.png"), animations: "disabled" });
  // For Aadhaar the file chooser comes first — a webcam rarely shows its QR code sharply — and the webcam stays below.
  // A passport's picture goes through the same chooser: the document check reads whichever it finds.
  await expect(page.getByRole("button", { name: "Use this computer's camera" })).toBeVisible();
  await page.getByLabel("Take or choose a picture of the QR code").setInputFiles(SPECIMEN);

  // Then a selfie, with the same challenge as a face check: the fake camera plays the passport's face.
  await expect(page.getByText("Now a short selfie")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start", exact: true })).toBeEnabled({ timeout: 15_000 });
  await page.getByRole("button", { name: "Start", exact: true }).click();
  try {
    await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible({ timeout: 120_000 });
  } catch (error) {
    // CI shows a failing test's message to anyone but its log only to people signed in, so say here what the page
    // showed instead, and what the API recorded.
    const shown = (
      await page
        .locator("main")
        .innerText()
        .catch(() => "(no page)")
    ).slice(0, 600);
    const recorded = await request.get(`${API}/v1/verification-sessions/${id}`, {
      headers: { Authorization: `Bearer ${process.env.E2E_API_KEY}` },
    });
    const { status, outcome } = await recorded.json();
    const probe = await probeDocumentCheck(request);
    throw new Error(
      `the check didn't finish: the page shows "${shown}"; the session is ${status}/${outcome}; ${probe}`,
      {
        cause: error,
      },
    );
  }
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

test("on a computer, the document is photographed with the webcam, looked at, then used (D43)", async ({
  page,
  request,
}, info) => {
  const { id, secret } = await steppedUp(request);
  await page.goto(`${VERIFY}/v/${id}#cs=${secret}`);
  await page.getByRole("button", { name: "Use my Aadhaar" }).click();
  await page.getByRole("button", { name: "Use this computer's camera" }).click();

  // The camera's picture with the guide, and what to do, said first.
  const take = page.getByRole("button", { name: "Take the photo" });
  await expect(take).toBeEnabled({ timeout: 15_000 });
  await expect(page.getByText("inside the frame")).toBeVisible();
  expect(await violations(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("1-document-camera.png"), animations: "disabled" });

  // A photo is shown before it is used; taking it again goes back to the camera.
  await take.click();
  await expect(page.getByRole("img", { name: "The photo of your document" })).toBeVisible();
  await expect(page.getByText("Can you read the lines at the bottom?")).toBeVisible();
  await page.getByRole("button", { name: "Take it again" }).click();
  await expect(take).toBeEnabled({ timeout: 15_000 });
  await take.click();
  await page.getByRole("button", { name: "Use this photo" }).click();

  // The photo goes on to the selfie, as a chosen file would.
  await expect(page.getByText("Now a short selfie")).toBeVisible();
});

test("the document camera can be left for the file chooser (D43)", async ({ page, request }) => {
  const { id, secret } = await steppedUp(request);
  await page.goto(`${VERIFY}/v/${id}#cs=${secret}`);
  await page.getByRole("button", { name: "Use my Aadhaar" }).click();
  await page.getByRole("button", { name: "Use this computer's camera" }).click();
  await page.getByRole("button", { name: "Choose a file instead" }).click();
  await expect(page.getByLabel("Take or choose a picture of the QR code")).toBeAttached();
  await expect(page.getByRole("button", { name: "Use this computer's camera" })).toBeVisible();
});

test("an Age Pass saved after one check answers the next check, with no camera", async ({
  page,
  request,
}, info) => {
  test.setTimeout(180_000);
  // Websites opt in through their own policy (decision D21): no preset accepts passes.
  const auth = { Authorization: `Bearer ${process.env.E2E_API_KEY}` };
  const policy = await request.post(`${API}/v1/policies`, {
    headers: auth,
    data: { name: "age_pass_18", min_age: 18, accept_age_pass: true },
  });
  expect(policy.status()).toBe(201);
  const session = async () => {
    const created = await request.post(`${API}/v1/verification-sessions`, {
      headers: auth,
      data: { policy: "age_pass_18" },
    });
    const { id, client_secret: secret } = await created.json();
    return { id: String(id), url: `${VERIFY}/v/${id}#cs=${secret}` };
  };

  // The first check: the camera, as always, then the offer to save passes in this browser.
  const first = await session();
  await page.goto(first.url);
  await expect(page.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Use your Age Pass" })).toHaveCount(0);
  await page.getByRole("button", { name: "Start the camera" }).click();
  await expect(page.getByRole("button", { name: "Start", exact: true })).toBeEnabled({ timeout: 15_000 });
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible({ timeout: 90_000 });
  await page.getByRole("button", { name: "Save an Age Pass" }).click();
  await expect(page.getByRole("status")).toContainText("Saved in this browser: 20 uses, until");
  await page.screenshot({ path: info.outputPath("1-saved.png"), animations: "disabled" });

  // The next check, in the same browser: a pass instead of the camera.
  const second = await session();
  await page.goto(second.url);
  await expect(page.getByRole("heading", { name: "Use your Age Pass" })).toBeVisible();
  expect(await violations(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("2-offered.png"), animations: "disabled" });
  await page.getByRole("button", { name: "Use my Age Pass" }).click();
  await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible();
  // A check decided by a pass gives out no new passes: a pass can't renew itself.
  await expect(page.getByRole("button", { name: "Save an Age Pass" })).toHaveCount(0);

  // The website's view: passed, and the token says how.
  const result = await (
    await request.get(`${API}/v1/verification-sessions/${second.id}`, { headers: auth })
  ).json();
  expect([result.status, result.outcome]).toEqual(["completed", "pass"]);
  const claims = JSON.parse(Buffer.from(result.age_token.split(".")[1], "base64url").toString());
  expect(claims.methods).toEqual(["age_pass"]);
});
