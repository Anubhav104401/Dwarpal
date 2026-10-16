/** The shop's own "age checked" pass: a cookie the shop signs itself, so a visitor can't forge or extend it. */

import { createHmac, timingSafeEqual } from "node:crypto";

export const PASS_COOKIE = "amber_pass";
export const PASS_LIFETIME_S = 30 * 60;
/** Remembers which check this browser started, so a return link only works in the browser that started it. */
export const PENDING_COOKIE = "amber_pending";

export interface Pass {
  sessionId: string;
  expiresAt: Date;
}

function signature(body: string, secret: string): string {
  return createHmac("sha256", secret).update(body).digest("base64url");
}

/** A pass for `sessionId`, valid for `PASS_LIFETIME_S` seconds: `<session>.<expiry>.<signature>`. */
export function issuePass(sessionId: string, secret: string, now: number = Date.now()): string {
  const body = `${sessionId}.${Math.floor(now / 1000) + PASS_LIFETIME_S}`;
  return `${body}.${signature(body, secret)}`;
}

/** The pass inside a cookie, or `null` if it is missing, forged, altered or expired. */
export function readPass(value: string | undefined, secret: string, now: number = Date.now()): Pass | null {
  const [sessionId, expiry, given, ...extra] = (value ?? "").split(".");
  if (sessionId === undefined || expiry === undefined || given === undefined || extra.length > 0) {
    return null;
  }
  const expected = Buffer.from(signature(`${sessionId}.${expiry}`, secret));
  const received = Buffer.from(given);
  if (received.length !== expected.length || !timingSafeEqual(received, expected)) {
    return null;
  }
  const expiresAt = new Date(Number(expiry) * 1000);
  return expiresAt.getTime() > now ? { sessionId, expiresAt } : null;
}
