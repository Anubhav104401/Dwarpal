import { describe, expect, it } from "vitest";

import { bandText, share, withinTarget } from "./figures";

describe("bandText", () => {
  it("says seconds up to a minute, minutes after, and 'or more' for the last band", () => {
    expect(bandText({ from: 10, to: 15 })).toBe("10–15 s");
    expect(bandText({ from: 45, to: 60 })).toBe("45–60 s");
    expect(bandText({ from: 60, to: 90 })).toBe("1–1.5 min");
    expect(bandText({ from: 300, to: null })).toBe("5 min or more");
  });
});

describe("withinTarget", () => {
  it("counts a band as within 15 s only if all of it is", () => {
    expect(
      [
        { from: 10, to: 15 },
        { from: 15, to: 20 },
        { from: 300, to: null },
      ].map(withinTarget),
    ).toEqual([true, false, false]);
  });
});

describe("share", () => {
  it("gives whole percentages, never hides a rare outcome, and has nothing to say before any decision", () => {
    const stage = { decided: 400, outcomes: { pass: 300, step_up: 99, reject: 1 }, median: null };
    expect([
      share(stage, "pass"),
      share(stage, "step_up"),
      share(stage, "reject"),
      share(stage, "fail"),
    ]).toEqual(["75 %", "25 %", "under 1 %", "0 %"]);
    expect(share({ decided: 0, outcomes: {}, median: null }, "pass")).toBe("—");
  });
});
