import {
  type CryptoKey,
  createLocalJWKSet,
  exportJWK,
  generateKeyPair,
  type JWK,
  type JWTPayload,
  SignJWT,
  UnsecuredJWT,
} from "jose";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { AgeTokenError, remoteKeys, type VerifyAgeTokenOptions, verifyAgeToken } from "../src/index.js";

const ISSUER = "http://localhost:8000";
const AUDIENCE = "prj_01M51KEEZTFP6T69S2YP831NV9";
const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";

let privateKey: CryptoKey;
let publicJwk: JWK;
let options: VerifyAgeTokenOptions;

beforeAll(async () => {
  const pair = await generateKeyPair("Ed25519");
  privateKey = pair.privateKey;
  publicJwk = { ...(await exportJWK(pair.publicKey)), kid: "sig_test", alg: "Ed25519", use: "sig" };
  options = {
    issuer: ISSUER,
    audience: AUDIENCE,
    minAge: 18,
    sessionId: SESSION,
    keys: createLocalJWKSet({ keys: [publicJwk] }),
  };
});

function claims(changes: JWTPayload = {}): JWTPayload {
  const base = { iss: ISSUER, aud: AUDIENCE, jti: "0192a6f0-0000-7000-8000-000000000000", sid: SESSION };
  return { ...base, outcome: "pass", age_over_18: true, policy: "uk_osa_18", livemode: false, ...changes };
}

async function sign(
  payload: JWTPayload,
  typ = "dwarpal-age+jwt",
  expires: number | string = "10m",
): Promise<string> {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "Ed25519", typ, kid: "sig_test" })
    .setIssuedAt()
    .setExpirationTime(expires)
    .sign(privateKey);
}

describe("verifyAgeToken", () => {
  it("allows entry for a passed check at exactly the required age", async () => {
    const verdict = await verifyAgeToken(await sign(claims()), options);
    expect(verdict.allowed).toBe(true);
    expect(verdict.outcome).toBe("pass");
    expect(verdict.sessionId).toBe(SESSION);
    expect(verdict.policy).toBe("uk_osa_18");
    expect(verdict.livemode).toBe(false);
    expect(verdict.expiresAt.getTime()).toBeGreaterThan(Date.now());
  });

  it("never allows entry for a failed check, whatever the age claim says", async () => {
    const failed = await verifyAgeToken(await sign(claims({ outcome: "fail", age_over_18: false })), options);
    const contradictory = await verifyAgeToken(await sign(claims({ outcome: "fail" })), options);
    expect(failed.allowed).toBe(false);
    expect(contradictory.allowed).toBe(false);
  });

  it("does not let a check for a lower age satisfy a higher requirement", async () => {
    const teen = claims({ age_over_13: true, policy: "teen_13" });
    delete teen.age_over_18;
    expect((await verifyAgeToken(await sign(teen), options)).allowed).toBe(false);
  });

  it("refuses tokens for someone else, of another type, or about another session", async () => {
    const token = await sign(claims());
    await expect(
      verifyAgeToken(token, { ...options, audience: "prj_SOMEONEELSE000000000000000" }),
    ).rejects.toThrow(AgeTokenError);
    await expect(verifyAgeToken(await sign(claims(), "JWT"), options)).rejects.toThrow(AgeTokenError);
    await expect(
      verifyAgeToken(token, { ...options, sessionId: "vs_01M51KF05CE4GSBH7F0G43G0ZZ" }),
    ).rejects.toThrow(/different session/);
  });

  it("refuses expired tokens", async () => {
    const expired = await sign(claims(), "dwarpal-age+jwt", Math.floor(Date.now() / 1000) - 60);
    await expect(verifyAgeToken(expired, options)).rejects.toThrow(AgeTokenError);
  });

  it("accepts only Ed25519 signatures: no shared secrets, and never no signature at all", async () => {
    const shared = await new SignJWT(claims())
      .setProtectedHeader({ alg: "HS256", typ: "dwarpal-age+jwt" })
      .setIssuedAt()
      .setExpirationTime("10m")
      .sign(new TextEncoder().encode("a-shared-secret-that-anyone-could-hold"));
    const unsigned = new UnsecuredJWT(claims()).setIssuedAt().setExpirationTime("10m").encode();
    await expect(verifyAgeToken(shared, options)).rejects.toThrow(AgeTokenError);
    await expect(verifyAgeToken(unsigned, options)).rejects.toThrow(AgeTokenError);
  });

  it("fetches the keys from another address when asked, and still checks the issuer exactly", async () => {
    const asked: string[] = [];
    vi.stubGlobal("fetch", async (input: string | URL | Request) => {
      asked.push(String(input));
      const headers = { "content-type": "application/json" };
      return new Response(JSON.stringify({ keys: [publicJwk] }), { status: 200, headers });
    });
    try {
      const privately = { ...options, keys: remoteKeys("http://api:8000/") };
      expect((await verifyAgeToken(await sign(claims()), privately)).allowed).toBe(true);
      expect(asked).toEqual(["http://api:8000/.well-known/jwks.json"]);
      expect(remoteKeys("http://api:8000")).toBe(privately.keys); // one cache per address
      // A token naming the private address as its issuer is still refused: the issuer is the public one.
      const misnamed = await sign(claims({ iss: "http://api:8000" }));
      await expect(verifyAgeToken(misnamed, privately)).rejects.toThrow(AgeTokenError);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("insists on a whole number of years", async () => {
    await expect(verifyAgeToken(await sign(claims()), { ...options, minAge: 17.5 })).rejects.toThrow(
      RangeError,
    );
  });
});
