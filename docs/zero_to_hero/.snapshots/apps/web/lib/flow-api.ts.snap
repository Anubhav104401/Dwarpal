/** The verify page's client for the Dwarpal flow API. After `start`, every call carries the session's flow token. */

export type SessionStatus = "in_progress" | "awaiting_step_up" | "completed";
export type AttemptOutcome = "pass" | "fail" | "step_up" | "retry" | "reject";

export interface FlowSession {
  id: string;
  status: SessionStatus;
  outcome: string | null;
  projectName: string;
  minAge: number;
  attemptsRemaining: number;
}

export interface AttemptResult {
  outcome: AttemptOutcome;
  reasons: string[];
  attemptsRemaining: number;
}

export interface CapturedFrame {
  image: Blob;
  tMs: number;
}

export class FlowError extends Error {
  override readonly name = "FlowError";
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

type Json = Record<string, unknown>;

const asJson = (value: unknown): Json => (typeof value === "object" && value !== null ? (value as Json) : {});
const asText = (value: unknown): string => (typeof value === "string" ? value : "");
const asCount = (value: unknown): number => (Number.isInteger(value) ? (value as number) : 0);

export class FlowClient {
  readonly #base: string;
  #token: string | null = null;

  constructor(apiUrl: string, sessionId: string) {
    this.#base = `${apiUrl.replace(/\/+$/, "")}/v1/flow/sessions/${encodeURIComponent(sessionId)}`;
  }

  /** Trade the link's one-time secret for a flow token, and learn what this session is about. */
  async start(clientSecret: string): Promise<FlowSession> {
    const data = await this.#post("/start", JSON.stringify({ client_secret: clientSecret }));
    this.#token = asText(data.flow_token);
    const session = asJson(data.session);
    return {
      id: asText(session.id),
      status: asText(session.status) as SessionStatus,
      outcome: typeof session.outcome === "string" ? session.outcome : null,
      projectName: asText(session.project_name),
      minAge: asCount(session.min_age),
      attemptsRemaining: asCount(session.attempts_remaining),
    };
  }

  /** One face attempt: fetch a fresh challenge, then upload the burst with it. */
  async attempt(frames: readonly CapturedFrame[]): Promise<AttemptResult> {
    const challenge = await this.#post("/challenge", null);
    const form = new FormData();
    form.set("challenge_id", asText(challenge.challenge_id));
    form.set(
      "meta",
      JSON.stringify({ frames: frames.map((frame, index) => ({ index, t_ms: Math.round(frame.tMs) })) }),
    );
    frames.forEach((frame, index) => {
      form.set(`frame_${index}`, frame.image, `frame_${index}.jpg`);
    });
    const data = await this.#post("/face-attempts", form);
    return {
      outcome: asText(data.outcome) as AttemptOutcome,
      reasons: Array.isArray(data.reasons) ? data.reasons.map(asText) : [],
      attemptsRemaining: asCount(data.attempts_remaining),
    };
  }

  /** Where to send the person now, or `null` if the website gave no address to return to. */
  async finish(): Promise<string | null> {
    const data = await this.#post("/finish", null);
    return typeof data.redirect_url === "string" ? data.redirect_url : null;
  }

  async #post(path: string, body: string | FormData | null): Promise<Json> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.#token !== null) {
      headers.Authorization = `Bearer ${this.#token}`;
    }
    if (typeof body === "string") {
      headers["Content-Type"] = "application/json";
    }
    let response: Response;
    try {
      response = await fetch(`${this.#base}${path}`, { method: "POST", headers, body });
    } catch {
      throw new FlowError(0, "network_error", "the server could not be reached", null);
    }
    const data = asJson(await response.json().catch(() => null));
    if (!response.ok) {
      const code = asText(data.code) || "http_error";
      const detail = asText(data.detail) || `the server answered ${response.status}`;
      throw new FlowError(response.status, code, detail, response.headers.get("x-request-id"));
    }
    return data;
  }
}
