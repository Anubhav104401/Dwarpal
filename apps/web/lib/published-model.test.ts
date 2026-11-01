import { describe, expect, it } from "vitest";

import { publishedModel, readPublishedModel } from "./published-model";

const ANSWER = {
  version: "age-convnext-tiny-2026.10.17",
  calibrated: false,
  calibration: { dataset: "utkface", faces: 11301 },
  thresholds: [
    {
      min_age: 18,
      risk_budget: 0.075,
      minor_bound: 0.07,
      adult_bound: 0.0099,
      adults: [{ ages: "18-20", faces: 330, pass: 0.13, step_up: 0.77, fail: 0.09 }],
    },
    { min_age: 13, risk_budget: 0.02 },
  ],
};

describe("the published model", () => {
  it("reads the API's answer, and a line never measured as having no bounds or bands", () => {
    const model = readPublishedModel(ANSWER);
    expect(model?.calibratedOn).toEqual({ name: "utkface", faces: 11301 });
    expect(model?.lines[0]).toEqual({
      minAge: 18,
      riskBudget: 0.075,
      minorBound: 0.07,
      adultBound: 0.0099,
      adults: [{ ages: "18-20", faces: 330, pass: 0.13, stepUp: 0.77, fail: 0.09 }],
    });
    expect(model?.lines[1]).toMatchObject({ minorBound: null, adultBound: null, adults: [] });
  });

  it("refuses an answer that isn't a model", () => {
    expect(readPublishedModel(null)).toBeNull();
    expect(readPublishedModel({ thresholds: [] })).toBeNull();
  });

  it("asks the API's public address, and answers null when the API fails or can't be reached", async () => {
    const asked: string[] = [];
    const answering = (status: number) =>
      (async (url: string) => {
        asked.push(url);
        return new Response(JSON.stringify(ANSWER), { status });
      }) as typeof fetch;
    expect((await publishedModel("http://api", answering(200)))?.version).toBe(ANSWER.version);
    expect(asked).toEqual(["http://api/v1/model"]);
    expect(await publishedModel("http://api", answering(503))).toBeNull();
    const down = (async () => {
      throw new TypeError("fetch failed");
    }) as typeof fetch;
    expect(await publishedModel("http://api", down)).toBeNull();
  });
});
