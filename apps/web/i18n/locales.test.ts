import { describe, expect, it } from "vitest";

import { isLocale, pickLocale } from "./locales";

describe("pickLocale", () => {
  it("keeps the person's own choice above everything", () => {
    expect(pickLocale("hi", "en-GB,en;q=0.9")).toBe("hi");
    expect(pickLocale("en", "hi-IN")).toBe("en");
  });

  it("otherwise follows the browser's languages, most wanted first", () => {
    expect(pickLocale(undefined, "hi-IN,hi;q=0.9,en;q=0.8")).toBe("hi");
    expect(pickLocale(undefined, "en-US,hi;q=0.5")).toBe("en");
    expect(pickLocale(undefined, "fr-FR,hi;q=0.7,en;q=0.6")).toBe("hi");
    expect(pickLocale(undefined, "en;q=0.4,hi;q=0.8")).toBe("hi");
  });

  it("falls back to English for anything else", () => {
    expect(pickLocale(undefined, null)).toBe("en");
    expect(pickLocale(undefined, "fr-FR,de;q=0.9")).toBe("en");
    expect(pickLocale("klingon", "")).toBe("en");
    expect(pickLocale(undefined, "hi;q=0")).toBe("en"); // q=0 means "not this one"
  });
});

describe("isLocale", () => {
  it("knows only the pages' languages", () => {
    expect(["en", "hi", "HI", "fr", 7, undefined].map(isLocale)).toEqual([
      true,
      true,
      false,
      false,
      false,
      false,
    ]);
  });
});
