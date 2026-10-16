import { describe, expect, it } from "vitest";

import { issuePass, PASS_LIFETIME_S, readPass } from "./pass";

const SECRET = "a-test-secret-that-is-long-enough-0123456789";
const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";
const NOW = Date.UTC(2026, 9, 16, 12, 0, 0);

describe("the shop's pass", () => {
  it("is accepted until it expires", () => {
    const pass = issuePass(SESSION, SECRET, NOW);
    expect(readPass(pass, SECRET, NOW)).toEqual({
      sessionId: SESSION,
      expiresAt: new Date(NOW + PASS_LIFETIME_S * 1000),
    });
    expect(readPass(pass, SECRET, NOW + PASS_LIFETIME_S * 1000)).toBeNull();
  });

  it("can't be forged, extended or moved to another session", () => {
    const pass = issuePass(SESSION, SECRET, NOW);
    const [session, expiry, signature] = pass.split(".");
    expect(readPass(pass, "a-different-secret-that-is-long-enough-9876", NOW)).toBeNull();
    expect(readPass(`${session}.${Number(expiry) + 3600}.${signature}`, SECRET, NOW)).toBeNull();
    expect(readPass(`vs_SOMEONEELSE00000000000000.${expiry}.${signature}`, SECRET, NOW)).toBeNull();
  });

  it("ignores missing and malformed cookies", () => {
    expect(readPass(undefined, SECRET, NOW)).toBeNull();
    expect(readPass("", SECRET, NOW)).toBeNull();
    expect(readPass("a.b.c.d", SECRET, NOW)).toBeNull();
  });
});
