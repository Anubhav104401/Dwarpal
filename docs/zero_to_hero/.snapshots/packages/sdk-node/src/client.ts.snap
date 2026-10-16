import { DwarpalApiError } from "./errors.js";

export const STATUSES = [
  "created",
  "in_progress",
  "awaiting_step_up",
  "completed",
  "expired",
  "canceled",
] as const;
export const OUTCOMES = ["pass", "fail", "reject", "step_up"] as const;
export type SessionStatus = (typeof STATUSES)[number];
export type SessionOutcome = (typeof OUTCOMES)[number];

export interface DwarpalClientOptions {
  /** Your secret API key, `dk_test_…` or `dk_live_…`. Use it only on your server, never in a browser. */
  apiKey: string;
  /** The Dwarpal API's address, such as `https://api.dwarpal.example`. */
  baseUrl: string;
  /** Give up on a request after this many milliseconds. Default: 10 seconds. */
  timeoutMs?: number;
  /** Replace the HTTP function, for tests. Default: the built-in `fetch`. */
  fetch?: typeof fetch;
}

export interface CreateSessionParams {
  policy?: string;
  returnUrl?: string;
  externalRef?: string;
}

export interface CreatedSession {
  id: string;
  status: SessionStatus;
  livemode: boolean;
  policy: string;
  /** Send the person here. The link carries a one-time secret: never log it or store it. */
  url: string;
  expiresAt: Date;
}

export interface SessionResult {
  id: string;
  status: SessionStatus;
  outcome: SessionOutcome | null;
  livemode: boolean;
  policy: string;
  minAge: number;
  attempts: number;
  externalRef: string | null;
  completedAt: Date | null;
  /** A signed age token once the session is completed. Check it with `verifyAgeToken` before trusting it. */
  ageToken: string | null;
}

type Json = Record<string, unknown>;

const API_KEY = /^dk_(test|live)_[A-Za-z0-9_-]{20,}$/;
const SESSION_ID = /^vs_[0-9A-Za-z]{26}$/;

function field<T>(data: Json, key: string, accept: (value: unknown) => value is T): T {
  const value = data[key];
  if (!accept(value)) {
    throw new TypeError(`the API's answer has an unexpected "${key}"`);
  }
  return value;
}

const isText = (value: unknown): value is string => typeof value === "string";
const isFlag = (value: unknown): value is boolean => typeof value === "boolean";
const isCount = (value: unknown): value is number => Number.isInteger(value);
const oneOf =
  <T extends string>(allowed: readonly T[]) =>
  (value: unknown): value is T =>
    allowed.includes(value as T);
const orNull =
  <T>(accept: (value: unknown) => value is T) =>
  (value: unknown): value is T | null =>
    value === null || accept(value);
const dateOrNull = (value: string | null): Date | null => (value === null ? null : new Date(value));

export class DwarpalClient {
  readonly #apiKey: string;
  readonly #baseUrl: string;
  readonly #timeoutMs: number;
  readonly #fetch: typeof fetch;

  constructor(options: DwarpalClientOptions) {
    if (!API_KEY.test(options.apiKey)) {
      throw new TypeError("apiKey must be a Dwarpal secret key: dk_test_… or dk_live_…");
    }
    this.#apiKey = options.apiKey;
    this.#baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.#timeoutMs = options.timeoutMs ?? 10_000;
    this.#fetch = options.fetch ?? globalThis.fetch;
  }

  /** Create a verification session, and get the link to send the person to. */
  async createSession(params: CreateSessionParams = {}): Promise<CreatedSession> {
    const body: Json = {};
    if (params.policy !== undefined) body.policy = params.policy;
    if (params.returnUrl !== undefined) body.return_url = params.returnUrl;
    if (params.externalRef !== undefined) body.external_ref = params.externalRef;
    const data = await this.#request("POST", "/v1/verification-sessions", body);
    return {
      id: field(data, "id", isText),
      status: field(data, "status", oneOf(STATUSES)),
      livemode: field(data, "livemode", isFlag),
      policy: field(data, "policy", isText),
      url: field(data, "url", isText),
      expiresAt: new Date(field(data, "expires_at", isText)),
    };
  }

  /** Read a session's result. A completed session comes with a freshly signed age token. */
  async retrieveSession(sessionId: string): Promise<SessionResult> {
    if (!SESSION_ID.test(sessionId)) {
      throw new TypeError("sessionId must be a Dwarpal session ID: vs_ followed by 26 characters");
    }
    const data = await this.#request("GET", `/v1/verification-sessions/${sessionId}`);
    return {
      id: field(data, "id", isText),
      status: field(data, "status", oneOf(STATUSES)),
      outcome: field(data, "outcome", orNull(oneOf(OUTCOMES))),
      livemode: field(data, "livemode", isFlag),
      policy: field(data, "policy", isText),
      minAge: field(data, "min_age", isCount),
      attempts: field(data, "attempts", isCount),
      externalRef: field(data, "external_ref", orNull(isText)),
      completedAt: dateOrNull(field(data, "completed_at", orNull(isText))),
      ageToken: field(data, "age_token", orNull(isText)),
    };
  }

  async #request(method: "GET" | "POST", path: string, body?: Json): Promise<Json> {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.#apiKey}`,
      Accept: "application/json",
    };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    const response = await this.#fetch(`${this.#baseUrl}${path}`, {
      method,
      headers,
      body: body === undefined ? null : JSON.stringify(body),
      signal: AbortSignal.timeout(this.#timeoutMs),
    });
    const parsed: unknown = await response.json().catch(() => null);
    const data: Json = typeof parsed === "object" && parsed !== null ? (parsed as Json) : {};
    if (!response.ok) {
      const code = typeof data.code === "string" ? data.code : "http_error";
      const detail = typeof data.detail === "string" ? data.detail : `the API answered ${response.status}`;
      throw new DwarpalApiError(response.status, code, detail, response.headers.get("x-request-id"));
    }
    return data;
  }
}
