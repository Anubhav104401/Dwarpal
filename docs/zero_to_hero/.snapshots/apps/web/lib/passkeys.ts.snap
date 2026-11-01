/**
 * Passkeys in the browser (Phase 9): the API sends WebAuthn's options as JSON, with binary values in base64url;
 * `navigator.credentials` wants those values as bytes, and answers in bytes. These functions translate both ways.
 * The checks happen on the server (services/api/src/dwarpal_api/domain/webauthn.py).
 */

type Json = Record<string, unknown>;

/** Base64url (no padding) to bytes. */
export function fromBase64Url(text: string): Uint8Array<ArrayBuffer> {
  const base64 = text.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(base64 + "=".repeat((4 - (base64.length % 4)) % 4));
  return Uint8Array.from(binary, (c) => c.charCodeAt(0));
}

/** Bytes to base64url (no padding), as the API expects them. */
export function toBase64Url(bytes: ArrayBuffer | Uint8Array): string {
  const view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let binary = "";
  for (const byte of view) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

const text = (value: unknown): string => (typeof value === "string" ? value : "");
const record = (value: unknown): Json => (typeof value === "object" && value !== null ? (value as Json) : {});

/** Whether this browser can make and use passkeys at all. */
export function passkeysSupported(): boolean {
  return typeof window !== "undefined" && typeof window.PublicKeyCredential === "function";
}

/** The API's registration options, as `navigator.credentials.create` takes them. */
export function creationOptions(options: Json): PublicKeyCredentialCreationOptions {
  const rp = record(options.rp);
  const user = record(options.user);
  const selection = record(options.authenticatorSelection);
  const params = Array.isArray(options.pubKeyCredParams) ? options.pubKeyCredParams.map(record) : [];
  const exclude = Array.isArray(options.excludeCredentials) ? options.excludeCredentials.map(record) : [];
  return {
    challenge: fromBase64Url(text(options.challenge)),
    rp: { id: text(rp.id), name: text(rp.name) },
    user: { id: fromBase64Url(text(user.id)), name: text(user.name), displayName: text(user.displayName) },
    pubKeyCredParams: params.map((p) => ({ type: "public-key", alg: Number(p.alg) })),
    authenticatorSelection: {
      residentKey: "required",
      requireResidentKey: true,
      userVerification: selection.userVerification === "required" ? "required" : "preferred",
    },
    attestation: "none",
    excludeCredentials: exclude.map((c) => ({ type: "public-key", id: fromBase64Url(text(c.id)) })),
    timeout: typeof options.timeout === "number" ? options.timeout : 300_000,
  };
}

/** The API's sign-in options, as `navigator.credentials.get` takes them: no account named, the device offers its
 * passkeys for this site. */
export function requestOptions(options: Json): PublicKeyCredentialRequestOptions {
  return {
    challenge: fromBase64Url(text(options.challenge)),
    rpId: text(options.rpId),
    userVerification: "required",
    timeout: typeof options.timeout === "number" ? options.timeout : 300_000,
  };
}

/** A new passkey's answer, for the API. */
export function registrationAnswer(credential: PublicKeyCredential): {
  client_data_json: string;
  attestation_object: string;
} {
  const response = credential.response as AuthenticatorAttestationResponse;
  return {
    client_data_json: toBase64Url(response.clientDataJSON),
    attestation_object: toBase64Url(response.attestationObject),
  };
}

/** A sign-in's answer, for the API. */
export function signInAnswer(credential: PublicKeyCredential): Json {
  const response = credential.response as AuthenticatorAssertionResponse;
  const answer: Json = {
    id: toBase64Url(credential.rawId),
    client_data_json: toBase64Url(response.clientDataJSON),
    authenticator_data: toBase64Url(response.authenticatorData),
    signature: toBase64Url(response.signature),
  };
  if (response.userHandle !== null && response.userHandle.byteLength > 0) {
    answer.user_handle = toBase64Url(response.userHandle);
  }
  return answer;
}

/** Whether a failure is the person closing the device's prompt (or it timing out): not worth an error message. */
export function cancelled(error: unknown): boolean {
  return error instanceof DOMException && (error.name === "NotAllowedError" || error.name === "AbortError");
}
