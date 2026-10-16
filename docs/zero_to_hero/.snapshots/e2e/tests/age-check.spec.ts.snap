import { expect, test } from "@playwright/test";

const SHOP = "http://localhost:3100";
const VERIFY = "http://localhost:3000";

test("an adult passes the age check and is let into the cellar", async ({ page }, info) => {
  await page.goto(SHOP);
  await page.getByRole("button", { name: "Verify my age to enter" }).click();

  await expect(page.getByRole("heading", { name: "Confirm you are 18 or over" })).toBeVisible();
  expect(page.url()).toMatch(/^http:\/\/localhost:3000\/v\/vs_[0-9A-Z]{26}$/);
  await page.screenshot({ path: info.outputPath("1-intro.png"), animations: "disabled" });

  await page.getByRole("button", { name: "Start the camera" }).click();
  await expect(page.getByRole("button", { name: "Take photos" })).toBeEnabled();
  await page.screenshot({ path: info.outputPath("2-camera.png"), animations: "disabled" });
  await page.getByRole("button", { name: "Take photos" }).click();
  await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: info.outputPath("3-passed.png"), animations: "disabled" });

  await page.getByRole("button", { name: /^Continue to / }).click();
  await expect(page).toHaveURL(`${SHOP}/cellar`);
  await expect(page.getByRole("status")).toContainText("Age verified");
  await page.screenshot({ path: info.outputPath("4-cellar.png"), fullPage: true, animations: "disabled" });
});

test("the cellar stays closed to anyone without a pass", async ({ page }) => {
  await page.goto(`${SHOP}/cellar`);
  await expect(page).toHaveURL(`${SHOP}/`);
  await expect(page.getByRole("button", { name: "Verify my age to enter" })).toBeVisible();
});

test("a verify link without its secret explains what to do", async ({ page }) => {
  await page.goto(`${VERIFY}/v/vs_01M51KF05CE4GSBH7F0G43G01V`);
  await expect(page.getByRole("heading", { name: "This link doesn't work" })).toBeVisible();
});

test("a return link only works in the browser that started the check", async ({ page }) => {
  await page.goto(`${SHOP}/age-check/complete?session_id=vs_01M51KF05CE4GSBH7F0G43G01V`);
  await expect(page).toHaveURL(`${SHOP}/refused?reason=other_browser`);
  await expect(
    page.getByRole("heading", { name: "Please finish the check where you started it" }),
  ).toBeVisible();
});
