import { describe, expect, it } from "vitest";

import { everyDay, shortDate } from "./daily";

describe("everyDay", () => {
  it("gives every day of the window, adds up policies, and ignores rows outside it", () => {
    const days = everyDay("2026-10-27", 3, [
      { day: "2026-10-27", outcome: "pass", sessions: 2 },
      { day: "2026-10-27", outcome: "pass", sessions: 1 },
      { day: "2026-10-29", outcome: "fail", sessions: 4 },
      { day: "2026-10-30", outcome: "pass", sessions: 9 },
    ]);

    expect(days.map((d) => d.day)).toEqual(["2026-10-27", "2026-10-28", "2026-10-29"]);
    expect(days.map((d) => d.total)).toEqual([3, 0, 4]);
    expect(days[0]?.counts).toEqual({ pass: 3 });
  });

  it("crosses a month's end, and gives nothing for a date it can't read", () => {
    expect(everyDay("2026-10-31", 2, []).map((d) => d.day)).toEqual(["2026-10-31", "2026-11-01"]);
    expect(everyDay("", 30, [])).toEqual([]);
  });
});

describe("shortDate", () => {
  it("writes the day and the month's short name", () => {
    expect(shortDate("2026-10-28")).toBe("28 Oct");
  });
});
