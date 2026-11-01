import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";

// The rules of WCAG 2.2 at levels A and AA, as axe-core tags them (earlier versions' rules included).
const STANDARDS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** Every accessibility rule the page breaks, as "rule — what it means — where"; empty when it breaks none. */
export async function violations(page: Page): Promise<string[]> {
  // Let one-off animations (a card fading in) finish: colours measured mid-fade are blends, not the page's colours.
  // Endless ones (a spinner) never finish, so they are left out.
  await page.evaluate(() =>
    Promise.all(
      document
        .getAnimations()
        .filter((a) => a.effect?.getTiming().iterations !== Number.POSITIVE_INFINITY)
        // An animation cancelled meanwhile (the page moved on) rejects its `finished`: that counts as done too.
        .map((a) => a.finished.catch(() => undefined)),
    ),
  );
  const results = await new AxeBuilder({ page }).withTags(STANDARDS).analyze();
  return results.violations.map(
    (v) => `${v.id} — ${v.help} — ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`,
  );
}
