/** The API refused a request. `code` is stable and meant for programs; `message` is meant for people. */
export class DwarpalApiError extends Error {
  override readonly name = "DwarpalApiError";
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(status: number, code: string, message: string, requestId: string | null) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

/** An age token failed verification: its signature, issuer, audience, type, age or session didn't check out. */
export class AgeTokenError extends Error {
  override readonly name = "AgeTokenError";
}

/** A webhook failed verification: its signature header was missing, malformed, too old, or didn't match. */
export class WebhookSignatureError extends Error {
  override readonly name = "WebhookSignatureError";
}
