import { describe, expect, it } from "vitest";

import {
  cancelled,
  creationOptions,
  fromBase64Url,
  registrationAnswer,
  requestOptions,
  signInAnswer,
  toBase64Url,
} from "./passkeys";

describe("base64url", () => {
  it("round-trips every byte value, without padding or + and /", () => {
    const bytes = Uint8Array.from({ length: 256 }, (_, i) => i);
    const encoded = toBase64Url(bytes);
    expect(encoded).not.toMatch(/[+/=]/);
    expect([...fromBase64Url(encoded)]).toEqual([...bytes]);
    for (const length of [0, 1, 2, 3, 4]) {
      const part = bytes.slice(0, length);
      expect([...fromBase64Url(toBase64Url(part))]).toEqual([...part]);
    }
  });
});

describe("options", () => {
  it("turns the API's registration options into bytes where the browser wants them", () => {
    const options = creationOptions({
      challenge: "AQID",
      rp: { id: "localhost", name: "Dwarpal console" },
      user: { id: "BAU", name: "a@b.example", displayName: "a@b.example" },
      pubKeyCredParams: [{ type: "public-key", alg: -8 }],
      authenticatorSelection: { userVerification: "required" },
      excludeCredentials: [{ type: "public-key", id: "Bgc" }],
      timeout: 1000,
    });
    expect([...(options.challenge as Uint8Array)]).toEqual([1, 2, 3]);
    expect([...(options.user.id as Uint8Array)]).toEqual([4, 5]);
    expect(options.pubKeyCredParams).toEqual([{ type: "public-key", alg: -8 }]);
    expect(options.authenticatorSelection?.userVerification).toBe("required");
    const excluded = options.excludeCredentials ?? [];
    expect(excluded.map((c) => [...(c.id as Uint8Array)])).toEqual([[6, 7]]);
    expect(options.attestation).toBe("none");
  });

  it("asks for a verified person when signing in, naming no account", () => {
    const options = requestOptions({ challenge: "AQID", rpId: "localhost" });
    expect(options.rpId).toBe("localhost");
    expect(options.userVerification).toBe("required");
    expect(options.allowCredentials).toBeUndefined();
  });
});

describe("answers", () => {
  const bytes = (...values: number[]) => Uint8Array.from(values).buffer;

  it("sends a new passkey's answer as base64url", () => {
    const credential = {
      response: { clientDataJSON: bytes(1), attestationObject: bytes(2) },
    } as unknown as PublicKeyCredential;
    expect(registrationAnswer(credential)).toEqual({ client_data_json: "AQ", attestation_object: "Ag" });
  });

  it("sends a sign-in's answer, with the account's handle only when the device gave one", () => {
    const response = { clientDataJSON: bytes(1), authenticatorData: bytes(2), signature: bytes(3) };
    const withHandle = { rawId: bytes(9), response: { ...response, userHandle: bytes(4) } };
    const without = { rawId: bytes(9), response: { ...response, userHandle: null } };
    expect(signInAnswer(withHandle as unknown as PublicKeyCredential)).toEqual({
      id: "CQ",
      client_data_json: "AQ",
      authenticator_data: "Ag",
      signature: "Aw",
      user_handle: "BA",
    });
    expect(signInAnswer(without as unknown as PublicKeyCredential)).not.toHaveProperty("user_handle");
  });

  it("treats a closed or timed-out prompt as cancelled, and other failures as errors", () => {
    expect(cancelled(new DOMException("closed", "NotAllowedError"))).toBe(true);
    expect(cancelled(new DOMException("aborted", "AbortError"))).toBe(true);
    expect(cancelled(new DOMException("bad", "SecurityError"))).toBe(false);
    expect(cancelled(new Error("x"))).toBe(false);
  });
});
