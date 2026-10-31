import { describe, expect, it } from "vitest";

import type { ModelLine } from "./console-api";
import { agesText, defaultLine, lineKey, lineLabel, percent } from "./projection";

const line = (minAge: number, riskBudget: number): ModelLine => ({
  minAge,
  riskBudget,
  tauPass: 0.9,
  tauFail: 0.1,
  minorBound: null,
  adultBound: null,
  adults: [],
});

describe("the policy editor's projection", () => {
  it("names a line by its age and risk budget", () => {
    expect(lineKey(line(18, 0.075))).toBe("18@0.075");
    expect(lineLabel(line(18, 0.075))).toBe("18+ · risk budget 7.5 %");
    expect(lineLabel(line(13, 0.15))).toBe("13+ · risk budget 15 %");
  });

  it("offers the 18+ line first, or else the model's first line", () => {
    expect(defaultLine([line(13, 0.15), line(18, 0.075)])?.minAge).toBe(18);
    expect(defaultLine([line(16, 0.15), line(21, 0.075)])?.minAge).toBe(16);
    expect(defaultLine([])).toBeUndefined();
  });

  it("writes age bands and shares as people do", () => {
    expect(agesText("18-20")).toBe("18–20");
    expect(agesText("30+")).toBe("30+");
    expect(percent(0.7727)).toBe("77 %");
    expect(percent(0.0019)).toBe("under 1 %");
    expect(percent(0)).toBe("0 %");
  });
});
