/** The policy editor's projection, in words: which line a choice means, and how adults fared at it. */

import type { ModelLine } from "./console-api";

/** A line's key in a form: its age and risk budget, which together pick exactly one of the model's lines. */
export const lineKey = (line: ModelLine): string => `${line.minAge}@${line.riskBudget}`;

/** A line as the editor offers it: "18+ · risk budget 7.5 %". */
export const lineLabel = (line: ModelLine): string =>
  `${line.minAge}+ · risk budget ${Number((line.riskBudget * 100).toFixed(1))} %`;

/** The line a form offers first: the 18+ line, which most websites need, or else the model's first. */
export function defaultLine(lines: readonly ModelLine[]): ModelLine | undefined {
  return lines.find((line) => line.minAge === 18) ?? lines[0];
}

/** An age band as people write it: "18-20" becomes "18–20" (an en dash), "30+" stays. */
export const agesText = (ages: string): string => ages.replace("-", "–");

/** A share as a whole percentage, with "under 1 %" for a share that rounds to 0 but isn't nothing. */
export function percent(rate: number): string {
  const whole = Math.round(rate * 100);
  return rate > 0 && whole === 0 ? "under 1 %" : `${whole} %`;
}
