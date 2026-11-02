import { describe, expect, it } from "vitest";

import { disclosuresOf, holderKey, lineFor, newKeys, presentation } from "./age-pass";
import { fromBase64Url, toBase64Url } from "./passkeys";

const encoder = new TextEncoder();
const encode = (value: unknown) => toBase64Url(encoder.encode(JSON.stringify(value)));
const decode = (text: string): unknown => JSON.parse(new TextDecoder().decode(fromBase64Url(text)));

/** A kept pass as the API sends it: a signed JWT (its signature isn't the browser's to check), then disclosures. */
function pass(lines: number[]): string {
  const disclosures = lines.map((line, i) => encode([`salt${i}`, `age_over_${line}`, true]));
  return `${encode({ typ: "dc+sd-jwt" })}.${encode({ vct: "urn:dwarpal:age-pass:1" })}.c2ln~${disclosures.join("~")}~`;
}

describe("a kept pass", () => {
  it("lists its disclosures by the claim each reveals", () => {
    expect([...disclosuresOf(pass([13, 16, 18])).keys()]).toEqual([
      "age_over_13",
      "age_over_16",
      "age_over_18",
    ]);
  });

  it("shows the lowest line that is enough, and none if no line is", () => {
    expect(lineFor([13, 16, 18], 15)).toBe(16);
    expect(lineFor([13, 16, 18], 18)).toBe(18);
    expect(lineFor([13, 16, 18], 21)).toBeNull();
  });
});

describe("keys", () => {
  it("keeps the private half unexportable and sends only the public key's four fields", async () => {
    const [pair] = await newKeys(1);
    if (pair === undefined) throw new Error("no key made");
    expect(pair.privateKey.extractable).toBe(false);
    await expect(crypto.subtle.exportKey("jwk", pair.privateKey)).rejects.toThrow();
    const key = await holderKey(pair.publicKey);
    expect(Object.keys(key).sort()).toEqual(["crv", "kty", "x", "y"]);
    expect([key.kty, key.crv, key.x.length, key.y.length]).toEqual(["EC", "P-256", 43, 43]);
  });
});

describe("a presentation", () => {
  it("reveals one line, and is signed with the pass's key over the nonce, the session and that line", async () => {
    const [pair] = await newKeys(1);
    if (pair === undefined) throw new Error("no key made");
    const kept = pass([13, 16, 18]);
    const now = Date.UTC(2026, 10, 2, 12);
    const shown = await presentation(kept, pair.privateKey, 18, "nonce-1", "vs_session", now);

    const parts = shown.split("~");
    expect(parts).toHaveLength(3); // the signed pass, one disclosure, the key-binding JWT
    expect(decode(parts[1] ?? "")).toEqual(["salt2", "age_over_18", true]);

    const [header, payload, signature] = (parts[2] ?? "").split(".");
    expect(decode(header ?? "")).toEqual({ alg: "ES256", typ: "kb+jwt" });
    const signedPart = `${parts[0]}~${parts[1]}~`;
    const hash = toBase64Url(await crypto.subtle.digest("SHA-256", encoder.encode(signedPart)));
    expect(decode(payload ?? "")).toEqual({
      iat: now / 1000,
      aud: "vs_session",
      nonce: "nonce-1",
      sd_hash: hash,
    });
    const valid = await crypto.subtle.verify(
      { name: "ECDSA", hash: "SHA-256" },
      pair.publicKey,
      fromBase64Url(signature ?? ""),
      encoder.encode(`${header}.${payload}`),
    );
    expect(valid).toBe(true);
  });

  it("can't show a line the pass doesn't state", async () => {
    const [pair] = await newKeys(1);
    if (pair === undefined) throw new Error("no key made");
    await expect(presentation(pass([13, 16]), pair.privateKey, 18, "n", "vs")).rejects.toThrow("18");
  });
});
