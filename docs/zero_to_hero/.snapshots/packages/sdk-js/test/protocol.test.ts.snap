import { describe, expect, it } from "vitest";

import { isOn, readMessage, readVerifyLink } from "../src/index.js";

const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";
const LINK = `https://verify.example/v/${SESSION}#cs=${SESSION}_secret_x`;

describe("readVerifyLink", () => {
  it("accepts a session's link, and finds its origin and session", () => {
    expect(readVerifyLink(LINK)).toEqual({ url: LINK, origin: "https://verify.example", sessionId: SESSION });
    expect(readVerifyLink(`http://localhost:3000/v/${SESSION}#cs=x`).origin).toBe("http://localhost:3000");
  });

  it.each([
    ["not a web address", "verify.example"],
    ["plain http away from this computer", `http://verify.example/v/${SESSION}#cs=x`],
    ["another path", `https://verify.example/console#cs=x`],
    ["a malformed session", "https://verify.example/v/vs_short#cs=x"],
    ["no secret", `https://verify.example/v/${SESSION}`],
    ["an empty secret", `https://verify.example/v/${SESSION}#cs=`],
  ])("refuses %s", (_, text) => {
    expect(() => readVerifyLink(text)).toThrow(TypeError);
  });
});

describe("readMessage", () => {
  const finished = {
    source: "dwarpal",
    type: "finished",
    sessionId: SESSION,
    redirectUrl: "https://shop.example/r",
  };

  it("reads the verify page's two messages", () => {
    expect(readMessage(finished)).toEqual(finished);
    expect(readMessage({ source: "dwarpal", type: "full_page", sessionId: SESSION })).toEqual({
      source: "dwarpal",
      type: "full_page",
      sessionId: SESSION,
    });
  });

  it("drops extra fields, so nothing unchecked gets through", () => {
    expect(readMessage({ ...finished, extra: "<script>" })).toEqual(finished);
  });

  it.each([
    ["nothing", null],
    ["text", "finished"],
    ["another sender's message", { ...finished, source: "someone" }],
    ["an unknown type", { ...finished, type: "passed" }],
    ["a malformed session", { ...finished, sessionId: "vs_1" }],
    ["a script address", { ...finished, redirectUrl: "javascript:alert(1)" }],
    ["no address", { source: "dwarpal", type: "finished", sessionId: SESSION }],
  ])("ignores %s", (_, data) => {
    expect(readMessage(data)).toBeNull();
  });
});

describe("isOn", () => {
  it("is true only for an address on the given origin", () => {
    expect(isOn("https://shop.example/age-check/complete?session_id=x", "https://shop.example")).toBe(true);
    expect(isOn("https://shop.example.evil/age-check", "https://shop.example")).toBe(false);
    expect(isOn("http://shop.example/age-check", "https://shop.example")).toBe(false);
    expect(isOn("not an address", "https://shop.example")).toBe(false);
  });
});
