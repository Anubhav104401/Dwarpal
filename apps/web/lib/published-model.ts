import type { AdultOutcome } from "./console-api";

/** One of the published model's lines: how well it keeps those under the age out and lets adults in. */
export interface PublishedLine {
  minAge: number;
  riskBudget: number;
  /** At most this share of people at any one age in the 5 years under the line pass (95 % confidence). */
  minorBound: number | null;
  /** At most this share of adults 3 or more years over the line are turned away (95 % confidence). */
  adultBound: number | null;
  adults: AdultOutcome[];
}

/** The age model's published performance: the API's `/v1/model`, which anyone may read. */
export interface PublishedModel {
  version: string;
  calibrated: boolean;
  calibratedOn: { name: string; faces: number | null } | null;
  lines: PublishedLine[];
}

type Json = Record<string, unknown>;

const isJson = (value: unknown): value is Json => typeof value === "object" && value !== null;
const number = (value: unknown): number | null => (typeof value === "number" ? value : null);
const list = (value: unknown): Json[] => (Array.isArray(value) ? value.filter(isJson) : []);

/** The API's answer as a `PublishedModel`, or null if it isn't one. Anything missing reads as "not measured". */
export function readPublishedModel(data: unknown): PublishedModel | null {
  if (!isJson(data) || typeof data.version !== "string") return null;
  const calibration = isJson(data.calibration) ? data.calibration : null;
  return {
    version: data.version,
    calibrated: data.calibrated === true,
    calibratedOn:
      calibration !== null && typeof calibration.dataset === "string"
        ? { name: calibration.dataset, faces: number(calibration.faces) }
        : null,
    lines: list(data.thresholds).map((line) => ({
      minAge: number(line.min_age) ?? 0,
      riskBudget: number(line.risk_budget) ?? 0,
      minorBound: number(line.minor_bound),
      adultBound: number(line.adult_bound),
      adults: list(line.adults).map((band) => ({
        ages: String(band.ages),
        faces: number(band.faces) ?? 0,
        pass: number(band.pass) ?? 0,
        stepUp: number(band.step_up) ?? 0,
        fail: number(band.fail) ?? 0,
      })),
    })),
  };
}

/** Ask the API for the model's performance; null when it can't be had, so the page says so instead of failing. */
export async function publishedModel(
  apiUrl: string,
  ask: typeof fetch = fetch,
): Promise<PublishedModel | null> {
  try {
    const answer = await ask(`${apiUrl}/v1/model`, { signal: AbortSignal.timeout(1500), cache: "no-store" });
    return answer.ok ? readPublishedModel(await answer.json()) : null;
  } catch {
    return null;
  }
}
