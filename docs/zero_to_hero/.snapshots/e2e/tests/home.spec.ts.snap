import { expect, test } from "@playwright/test";

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
