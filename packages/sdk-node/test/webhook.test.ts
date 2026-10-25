import { createHmac } from "node:crypto";

import { describe, expect, it } from "vitest";

import { verifyWebhook, WebhookSignatureError } from "../src/index.js";

const SECRET = "whsec_test_only_secret";
const NOW = new Date("2026-10-25T12:00:00Z");
const T = Math.floor(NOW.getTime() / 1000);
const BODY =
  '{"id":"evt_1","object":"event","type":"verification_session.completed","data":{"outcome":"pass"}}';

function header(body: string, timestamp = T, secret = SECRET): string {
  const digest = createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
  return `t=${timestamp},v1=${digest}`;
}

describe("verifyWebhook", () => {
  it("returns the event when the signature, the secret and the time all check out", () => {
    const event = verifyWebhook(BODY, header(BODY), SECRET, { now: NOW });
    expect(event.type).toBe("verification_session.completed");
    expect(event.data.outcome).toBe("pass");
  });

  it("refuses a body changed by even one character", () => {
    const changed = BODY.replace("pass", "fail");
    expect(() => verifyWebhook(changed, header(BODY), SECRET, { now: NOW })).toThrow(WebhookSignatureError);
  });

  it("refuses a signature made with another secret", () => {
    expect(() => verifyWebhook(BODY, header(BODY, T, "whsec_other"), SECRET, { now: NOW })).toThrow(
      /does not match/,
    );
  });

  it("refuses a signature older than five minutes, so a captured webhook can't be replayed later", () => {
    expect(() => verifyWebhook(BODY, header(BODY, T - 301), SECRET, { now: NOW })).toThrow(/too old/);
    expect(verifyWebhook(BODY, header(BODY, T - 299), SECRET, { now: NOW }).id).toBe("evt_1");
  });

  it("refuses a missing or malformed header", () => {
    for (const bad of [undefined, "", "t=abc,v1=00", `t=${T}`, `v1=${"0".repeat(64)}`]) {
      expect(() => verifyWebhook(BODY, bad, SECRET, { now: NOW })).toThrow(/malformed/);
    }
  });
});
