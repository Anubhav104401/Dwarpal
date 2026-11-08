import { describe, expect, it } from "vitest";

import { originLines } from "./origins";

describe("originLines", () => {
  it("takes one origin per line, trimmed, and skips blank lines, whatever the line endings", () => {
    expect(originLines("https://shop.example\r\n\n  http://localhost:3100  \n")).toEqual([
      "https://shop.example",
      "http://localhost:3100",
    ]);
  });

  it("gives an empty list for an empty box", () => {
    expect(originLines("  \n ")).toEqual([]);
  });
});
