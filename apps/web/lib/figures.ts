/** The dashboard's headline figures, as words: how long the face checks' median took, shares of their outcomes, and
 * how the ID-document checks after them went. */

import type { DocumentStage, FaceStage } from "./console-api";

/** The design's target for the median time to a decision, in seconds (NFR-02). */
export const MEDIAN_TARGET_S = 15;

/** A band of seconds as people say it: "10–15 s", "1–1.5 min", or "5 min or more". */
export function bandText(band: { from: number; to: number | null }): string {
  const minutes = (seconds: number) => `${Number((seconds / 60).toFixed(1))}`;
  if (band.to === null)
    return band.from >= 60 ? `${minutes(band.from)} min or more` : `${band.from} s or more`;
  if (band.to <= 60) return `${band.from}–${band.to} s`;
  return `${minutes(band.from)}–${minutes(band.to)} min`;
}

/** Whether the median band is within the target: only if the whole band is. */
export const withinTarget = (band: { from: number; to: number | null }): boolean =>
  band.to !== null && band.to <= MEDIAN_TARGET_S;

/** `count` as a whole percentage of `whole` ("12 %"), or "—" when the whole is nothing. A share that rounds to 0 but
 * isn't nothing reads "under 1 %", so a rare outcome isn't hidden; and none reads over 100 % — a check opened before
 * the days shown can end within them. */
export function percent(count: number, whole: number): string {
  if (whole <= 0) return "—";
  const rounded = Math.min(Math.round((count / whole) * 100), 100);
  return count > 0 && rounded === 0 ? "under 1 %" : `${rounded} %`;
}

/** One outcome's share of the decided face checks. */
export const share = (stage: FaceStage, outcome: string): string =>
  percent(stage.outcomes[outcome] ?? 0, stage.decided);

/** The ID-document checks: of those reached, the share that ended — the design's step-up conversion — the share that
 * passed (by the document, or by an Age Pass in a check that starts there), and the share that left or is still on it. */
export function documentFigures(stage: DocumentStage): { finished: string; passed: string; left: string } {
  const ended = Object.values(stage.outcomes).reduce((sum, count) => sum + count, 0);
  const passed = (stage.outcomes.pass ?? 0) + (stage.outcomes.age_pass ?? 0);
  return {
    finished: percent(ended, stage.opened),
    passed: percent(passed, stage.opened),
    left: percent(Math.max(stage.opened - ended, 0), stage.opened),
  };
}
