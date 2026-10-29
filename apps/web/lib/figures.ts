/** The dashboard's headline figures about face checks, as words: how long the median took, and shares of outcomes. */

import type { FaceStage } from "./console-api";

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

/** One outcome's share of the decided face checks, as a whole percentage ("12 %"), or "—" when nothing has been
 * decided. A share that rounds to 0 but isn't nothing reads "under 1 %", so a rare outcome isn't hidden. */
export function share(stage: FaceStage, outcome: string): string {
  if (stage.decided === 0) return "—";
  const count = stage.outcomes[outcome] ?? 0;
  const percent = Math.round((count / stage.decided) * 100);
  return count > 0 && percent === 0 ? "under 1 %" : `${percent} %`;
}
