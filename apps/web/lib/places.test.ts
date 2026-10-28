import { describe, expect, it } from "vitest";

import { matching, PLACES, type Place } from "./places";

const shop: Place = { label: "Amber Cellars", href: "/console/org_1", hint: "Organisation" };
const project: Place = {
  label: "Default project",
  href: "/console/org_1/prj_1",
  hint: "Project in Amber Cellars",
};

describe("matching", () => {
  it("gives everything, in order, when nothing is typed", () => {
    expect(matching([...PLACES, shop], "  ")).toEqual([...PLACES, shop]);
  });

  it("needs every word, in any order and case, from the label or the hint", () => {
    expect(matching([...PLACES, shop, project], "CELLARS project")).toEqual([project]);
    expect(matching([...PLACES, shop, project], "recovery")).toEqual([PLACES[2]]);
    expect(matching([...PLACES, shop, project], "nowhere")).toEqual([]);
  });

  it("puts places whose name starts with the first word ahead of the rest", () => {
    expect(matching([project, shop], "amber").map((p) => p.label)).toEqual([
      "Amber Cellars",
      "Default project",
    ]);
  });
});
