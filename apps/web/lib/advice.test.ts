import { describe, expect, it } from "vitest";

import { DEFAULT_PROBLEM, DEFAULT_TIP, problemFor, tipFor } from "./advice";

describe("tipFor", () => {
  it("gives the tip for the first reason it knows", () => {
    expect(tipFor(["too_dark"])).toMatch(/too dark/);
    expect(tipFor(["something_new", "no_face"])).toMatch(/couldn't see a face/);
  });

  it("falls back to a general tip for unknown or missing reasons", () => {
    expect(tipFor([])).toBe(DEFAULT_TIP);
    expect(tipFor(["verification_failed"])).toBe(DEFAULT_TIP);
  });
});

describe("problemFor", () => {
  it("explains known problems and never shows raw codes", () => {
    expect(problemFor("session_not_open").title).toBe("This age check has ended");
    expect(problemFor("camera_blocked").detail).toMatch(/camera access/);
    expect(problemFor("internal_error")).toBe(DEFAULT_PROBLEM);
  });
});
