import { describe, expect, it } from "vitest";

import en from "../messages/en.json";
import hi from "../messages/hi.json";
import { DEFAULT, problemFor, tipFor } from "./advice";

describe("tipFor", () => {
  it("gives the tip for the first reason it knows", () => {
    expect(tipFor(["too_dark"])).toBe("too_dark");
    expect(tipFor(["something_new", "no_face"])).toBe("no_face");
  });

  it("falls back to a general tip for unknown or missing reasons", () => {
    expect(tipFor([])).toBe(DEFAULT);
    expect(tipFor(["verification_failed"])).toBe(DEFAULT);
  });
});

describe("problemFor", () => {
  it("names known problems and never passes a raw code on", () => {
    expect(problemFor("session_not_open")).toBe("session_not_open");
    expect(problemFor("internal_error")).toBe(DEFAULT);
  });
});

describe("the words", () => {
  const codes = [
    ...["too_dark", "liveness_check_failed", "mrz_not_found", "face_mismatch", "analysis_unavailable"].map(
      (reason) => tipFor([reason]),
    ),
    DEFAULT,
  ];

  it("exist in every language for every tip and problem", () => {
    for (const messages of [en, hi]) {
      for (const code of codes) {
        expect(messages.Tips[code as keyof typeof messages.Tips]).toBeTruthy();
      }
      expect(
        messages.Problems[problemFor("camera_blocked") as keyof typeof messages.Problems].title,
      ).toBeTruthy();
    }
  });

  it("have the same keys in Hindi as in English, everywhere", () => {
    const keys = (value: unknown, path = ""): string[] =>
      typeof value === "object" && value !== null
        ? Object.entries(value).flatMap(([key, child]) => keys(child, `${path}.${key}`))
        : [path];
    expect(keys(hi).sort()).toEqual(keys(en).sort());
  });
});
