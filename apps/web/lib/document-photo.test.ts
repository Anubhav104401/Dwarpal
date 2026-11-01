import { describe, expect, it } from "vitest";

import { fitWithin, MAX_DOCUMENT_SIDE, QUALITIES } from "./document-photo";

describe("fitWithin", () => {
  it("scales a large photo down so its longer side fits, keeping its shape", () => {
    expect(fitWithin(4000, 3000, MAX_DOCUMENT_SIDE)).toEqual({ width: 2000, height: 1500 });
    expect(fitWithin(3000, 4000, MAX_DOCUMENT_SIDE)).toEqual({ width: 1500, height: 2000 });
  });

  it("never enlarges a small photo", () => {
    expect(fitWithin(1200, 900, MAX_DOCUMENT_SIDE)).toEqual({ width: 1200, height: 900 });
  });

  it("never draws a side of zero, however thin the picture", () => {
    expect(fitWithin(10000, 1, MAX_DOCUMENT_SIDE)).toEqual({ width: 2000, height: 1 });
  });
});

describe("QUALITIES", () => {
  it("are tried from the best down", () => {
    expect([...QUALITIES]).toEqual([...QUALITIES].sort((a, b) => b - a));
  });
});
