import { createHmac, timingSafeEqual } from "node:crypto";

import { WebhookSignatureError } from "./errors.js";

/** How old a signature may be, by default: five minutes. Older ones are refused as possible replays. */
export const WEBHOOK_TOLERANCE_S = 300;

/** What Dwarpal sends: one event, as it was when it happened. */
export interface DwarpalEvent {
  id: string;
  object: "event";
  type: string;
  livemode: boolean;
  created_at: string;
  data: Record<string, unknown>;
}

export interface VerifyWebhookOptions {
  /** How many seconds old a signature may be. */
  toleranceS?: number;
  /** The current time, for tests. */
  now?: Date;
}

/**
 * Check that a webhook really came from Dwarpal, and is recent, then return its event.
 * Pass the body exactly as it arrived: parsing and re-serialising JSON changes the bytes, and the signature with them.
 */
export function verifyWebhook(
  rawBody: string | Uint8Array,
  signatureHeader: string | null | undefined,
  secret: string,
  options: VerifyWebhookOptions = {},
): DwarpalEvent {
  const fields = parseHeader(signatureHeader ?? "");
  const timestamp = Number(fields.get("t"));
  const given = fields.get("v1");
  if (!Number.isInteger(timestamp) || given === undefined || !/^[0-9a-f]{64}$/.test(given)) {
    throw new WebhookSignatureError("the Dwarpal-Signature header is missing or malformed");
  }
  const now = Math.floor((options.now ?? new Date()).getTime() / 1000);
  if (Math.abs(now - timestamp) > (options.toleranceS ?? WEBHOOK_TOLERANCE_S)) {
    throw new WebhookSignatureError("the signature is too old, or from the future: this may be a replay");
  }
  const body = typeof rawBody === "string" ? Buffer.from(rawBody, "utf8") : Buffer.from(rawBody);
  const expected = createHmac("sha256", secret).update(`${timestamp}.`).update(body).digest();
  // Compared in constant time, so the time taken reveals nothing about how much of a forgery was right.
  if (!timingSafeEqual(expected, Buffer.from(given, "hex"))) {
    throw new WebhookSignatureError("the signature does not match: the body or the secret is wrong");
  }
  return JSON.parse(body.toString("utf8")) as DwarpalEvent;
}

function parseHeader(header: string): Map<string, string> {
  const fields = new Map<string, string>();
  for (const part of header.split(",")) {
    const at = part.indexOf("=");
    if (at > 0) fields.set(part.slice(0, at).trim(), part.slice(at + 1).trim());
  }
  return fields;
}
