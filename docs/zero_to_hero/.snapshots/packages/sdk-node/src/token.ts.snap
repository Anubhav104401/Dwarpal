import { createRemoteJWKSet, errors, type JWTPayload, type JWTVerifyGetKey, jwtVerify } from "jose";

import { AgeTokenError } from "./errors.js";

/** The only signature algorithm Dwarpal uses, by its RFC 9864 name. Tokens claiming any other are refused. */
export const ALGORITHM = "Ed25519";
/** The type every Dwarpal age token declares in its header. */
export const TOKEN_TYPE = "dwarpal-age+jwt";

export type Outcome = "pass" | "fail" | "reject";

export interface VerifyAgeTokenOptions {
  /** The API's issuer address, exactly as in its discovery document. */
  issuer: string;
  /** Your project's ID (`prj_…`). Tokens addressed to anyone else are refused. */
  audience: string;
  /** The minimum age your site requires. Only a token stating `age_over_<minAge>: true` allows entry. */
  minAge: number;
  /** The session you expect, from the redirect back to your site. A token about any other session is refused. */
  sessionId?: string;
  /** Where the public keys come from. By default they are fetched from the issuer, cached, and refetched for a new key. */
  keys?: JWTVerifyGetKey;
}

export interface AgeVerdict {
  /** True only if the check passed for exactly the age you asked about. */
  allowed: boolean;
  outcome: Outcome;
  sessionId: string;
  policy: string;
  livemode: boolean;
  expiresAt: Date;
}

const keySets = new Map<string, JWTVerifyGetKey>();

/**
 * The public keys of the Dwarpal API at `baseUrl` (its `/.well-known/jwks.json`): fetched when first needed, kept,
 * and fetched again for a key not seen yet. A token's keys come from its issuer by default; pass these as `keys`
 * when your server reaches Dwarpal by another address — over a private network, say.
 */
export function remoteKeys(baseUrl: string): JWTVerifyGetKey {
  const base = baseUrl.replace(/\/+$/, "");
  let keys = keySets.get(base);
  if (keys === undefined) {
    keys = createRemoteJWKSet(new URL(`${base}/.well-known/jwks.json`));
    keySets.set(base, keys);
  }
  return keys;
}

async function verifiedClaims(token: string, options: VerifyAgeTokenOptions): Promise<JWTPayload> {
  try {
    const { payload } = await jwtVerify(token, options.keys ?? remoteKeys(options.issuer), {
      issuer: options.issuer,
      audience: options.audience,
      algorithms: [ALGORITHM],
      typ: TOKEN_TYPE,
      requiredClaims: ["exp", "iat", "jti", "sid", "outcome"],
    });
    return payload;
  } catch (error) {
    if (error instanceof errors.JOSEError) {
      throw new AgeTokenError(`the age token is not valid (${error.code})`, { cause: error });
    }
    throw error;
  }
}

/** Check an age token's signature and claims, and say whether it allows entry at `minAge`. Throws if it is invalid. */
export async function verifyAgeToken(token: string, options: VerifyAgeTokenOptions): Promise<AgeVerdict> {
  if (!Number.isInteger(options.minAge) || options.minAge < 1) {
    throw new RangeError("minAge must be a whole number of years, such as 18");
  }
  const claims = await verifiedClaims(token, options);
  const { outcome, sid, exp } = claims;
  if (outcome !== "pass" && outcome !== "fail" && outcome !== "reject") {
    throw new AgeTokenError("the age token has an unknown outcome");
  }
  if (typeof sid !== "string" || (options.sessionId !== undefined && sid !== options.sessionId)) {
    throw new AgeTokenError("the age token describes a different session");
  }
  return {
    allowed: outcome === "pass" && claims[`age_over_${options.minAge}`] === true,
    outcome,
    sessionId: sid,
    policy: typeof claims.policy === "string" ? claims.policy : "",
    livemode: claims.livemode === true,
    expiresAt: new Date((exp ?? 0) * 1000),
  };
}
