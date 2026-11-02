/**
 * The console's client for Dwarpal's console API. Requests go to /console-api on this site, which Next.js passes on to
 * the API (next.config.ts), so the session cookie stays on one origin. Every change repeats the CSRF token from /me.
 */

import type { DailyCount } from "./daily";

export type Role = "owner" | "admin" | "developer" | "analyst";

export interface Organisation {
  id: string;
  name: string;
  role: Role;
}

export interface Me {
  id: string;
  email: string;
  totpEnabled: boolean;
  recoveryCodesLeft: number;
  organisations: Organisation[];
}

export interface Member {
  user: string;
  email: string;
  role: Role;
}

/** A new authenticator secret, not yet in force: the text to type in, and the otpauth:// address apps read. */
export interface TotpOffer {
  secret: string;
  uri: string;
}

/** A passkey on the account: the person's label for it, and when it was added and last used. */
export interface PasskeyInfo {
  id: string;
  name: string;
  createdAt: string;
  lastUsedAt: string | null;
}

export interface Project {
  id: string;
  name: string;
  allowedOrigins: string[];
  retentionDays: number;
}

export interface NewKey {
  id: string;
  key: string;
  scopes: string[];
  livemode: boolean;
}

export interface AuditEntry {
  seq: number;
  actor: string;
  action: string;
  target: string;
  createdAt: string;
}

export interface AuditLog {
  entries: AuditEntry[];
  intact: boolean;
  firstBroken: number | null;
}

export interface SessionSummary {
  id: string;
  status: string;
  outcome: string | null;
  policy: string;
  attempts: number;
  externalRef: string | null;
  createdAt: string;
}

/** Which sessions to list: by outcome, and by the website's own reference; an empty field means any. */
export interface SessionSearch {
  outcome?: string | undefined;
  externalRef?: string | undefined;
}

export interface SessionPage {
  sessions: SessionSummary[];
  nextCursor: string | null;
}

/** One attempt as the decision saw it: its outcome, reasons and the numbers behind them — never an image. */
export interface TracedAttempt {
  kind: string;
  outcome: string;
  reasons: string[];
  scores: Record<string, unknown>;
  createdAt: string;
}

export interface SessionTrace extends SessionSummary {
  traced: TracedAttempt[];
}

/** How adults in one age band above a line fared on the test split: shares that passed, were sent to a stronger
 * check, or failed, out of `faces`. */
export interface AdultOutcome {
  ages: string;
  faces: number;
  pass: number;
  stepUp: number;
  fail: number;
}

/** One age's lines: pass at or above `tauPass`, fail at or below `tauFail`, a second check in between. */
export interface ModelLine {
  minAge: number;
  riskBudget: number;
  tauPass: number;
  tauFail: number;
  minorBound: number | null;
  adultBound: number | null;
  /** The policy editor's projection; empty when the model in use hasn't been measured. */
  adults: AdultOutcome[];
}

/** Where a set of faces and their ages came from. */
export interface FaceSource {
  name: string;
  licence: string;
  ageSource: string;
  faces: number | null;
}

export interface ModelInfo {
  version: string;
  calibrated: boolean;
  note: string | null;
  permittedUse: string | null;
  backbone: string | null;
  trainedOn: FaceSource | null;
  calibratedOn: FaceSource | null;
  lines: ModelLine[];
}

/** How the face checks that reached a decision ended, and the band of time holding the median (lib/figures.ts). */
export interface FaceStage {
  decided: number;
  outcomes: Record<string, number>;
  median: { from: number; to: number | null } | null;
}

export interface Analytics {
  since: string;
  totals: Record<string, number>;
  daily: DailyCount[];
  faceStage: FaceStage;
}

export interface PolicyVersion {
  id: string;
  preset: boolean;
  minAge: number;
  riskBudget: number;
  maxFaceAttempts: number;
  /** Sessions under this version accept Age Passes and give them out (Phase 9, D21). */
  acceptAgePass: boolean;
}

/** The events a webhook endpoint can subscribe to (app/webhooks.py). */
export const EVENT_TYPES = ["verification_session.completed", "verification_session.expired"] as const;

export interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  enabled: boolean;
  createdAt: string;
}

/** A just-created endpoint: the only time its signing secret is shown. */
export interface NewWebhook extends WebhookEndpoint {
  secret: string;
}

export interface Delivery {
  id: string;
  event: string;
  status: string;
  attempt: number;
  lastStatus: number | null;
  lastError: string | null;
  createdAt: string;
}

/** What each role may do, as the API decides it (domain/roles.py); the pages only use it to hide what would fail. */
export const CAN = {
  manageMembers: (role: Role) => role === "owner" || role === "admin",
  readAudit: (role: Role) => role === "owner" || role === "admin",
  manageKeys: (role: Role) => role !== "analyst",
  managePolicies: (role: Role) => role !== "analyst",
  manageWebhooks: (role: Role) => role !== "analyst",
} as const;

export class ConsoleError extends Error {
  override readonly name = "ConsoleError";
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

type Json = Record<string, unknown>;

const asJson = (value: unknown): Json => (typeof value === "object" && value !== null ? (value as Json) : {});
const asText = (value: unknown): string => (typeof value === "string" ? value : "");
const asList = (value: unknown): Json[] => (Array.isArray(value) ? value.map(asJson) : []);
const asCount = (value: unknown): number => (typeof value === "number" ? value : 0);
const asTexts = (value: unknown): string[] => (Array.isArray(value) ? value.map(asText) : []);
const orNull = (value: unknown): string | null => (typeof value === "string" ? value : null);
const orNumber = (value: unknown): number | null => (typeof value === "number" ? value : null);

function asFaceSource(value: unknown, nameKey: string): FaceSource | null {
  if (typeof value !== "object" || value === null) return null;
  const s = asJson(value);
  return {
    name: asText(s[nameKey]),
    licence: asText(s.licence),
    ageSource: asText(s.age_source),
    faces: orNumber(s.faces),
  };
}

function asSession(s: Json): SessionSummary {
  return {
    id: asText(s.id),
    status: asText(s.status),
    outcome: orNull(s.outcome),
    policy: asText(s.policy),
    attempts: asCount(s.attempts),
    externalRef: orNull(s.external_ref),
    createdAt: asText(s.created_at),
  };
}

function asEndpoint(e: Json): WebhookEndpoint {
  return {
    id: asText(e.id),
    url: asText(e.url),
    events: asTexts(e.events),
    enabled: e.enabled === true,
    createdAt: asText(e.created_at),
  };
}

const asRole = (value: unknown): Role =>
  value === "owner" || value === "admin" || value === "developer" ? value : "analyst";

export class ConsoleClient {
  readonly #base: string;
  #csrf = "";

  constructor(base = "/console-api") {
    this.#base = base.replace(/\/+$/, "");
  }

  async #call(method: string, path: string, body?: unknown): Promise<Json> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET") headers["X-CSRF-Token"] = this.#csrf;
    const response = await fetch(`${this.#base}${path}`, {
      method,
      headers,
      body: body === undefined ? null : JSON.stringify(body),
      credentials: "same-origin",
      cache: "no-store",
    });
    const data = response.status === 204 ? {} : asJson(await response.json().catch(() => ({})));
    if (!response.ok) {
      throw new ConsoleError(
        response.status,
        asText(data.code) || "http_error",
        asText(data.detail) || "failed",
      );
    }
    return data;
  }

  #remember(data: Json): Me {
    this.#csrf = asText(data.csrf_token);
    return {
      id: asText(data.id),
      email: asText(data.email),
      totpEnabled: data.totp_enabled === true,
      recoveryCodesLeft: asCount(data.recovery_codes_left),
      organisations: asList(data.organisations).map((o) => ({
        id: asText(o.id),
        name: asText(o.name),
        role: asRole(o.role),
      })),
    };
  }

  /** Who is signed in, or null when nobody is. */
  async me(): Promise<Me | null> {
    try {
      return this.#remember(await this.#call("GET", "/me"));
    } catch (error) {
      if (error instanceof ConsoleError && error.status === 401) return null;
      throw error;
    }
  }

  async signIn(email: string, password: string, code?: string): Promise<Me> {
    const body: Json = { email, password };
    if (code) body.code = code;
    return this.#remember(await this.#call("POST", "/login", body));
  }

  async signUp(email: string, password: string, organisation: string): Promise<Me> {
    return this.#remember(await this.#call("POST", "/signup", { email, password, organisation }));
  }

  async signOut(): Promise<void> {
    await this.#call("POST", "/logout");
    this.#csrf = "";
  }

  async members(org: string): Promise<Member[]> {
    const data = await this.#call("GET", `/orgs/${encodeURIComponent(org)}/members`);
    return asList(data.data).map((m) => ({
      user: asText(m.user),
      email: asText(m.email),
      role: asRole(m.role),
    }));
  }

  async addMember(org: string, email: string, role: Role): Promise<void> {
    await this.#call("POST", `/orgs/${encodeURIComponent(org)}/members`, { email, role });
  }

  async changeRole(org: string, user: string, role: Role): Promise<void> {
    await this.#call("PATCH", `/orgs/${encodeURIComponent(org)}/members/${encodeURIComponent(user)}`, {
      role,
    });
  }

  async removeMember(org: string, user: string): Promise<void> {
    await this.#call("DELETE", `/orgs/${encodeURIComponent(org)}/members/${encodeURIComponent(user)}`);
  }

  /** Start setting up one-time codes: a new secret, in force only once a code from it is confirmed. */
  async totpEnrol(): Promise<TotpOffer> {
    const data = await this.#call("POST", "/totp");
    return { secret: asText(data.secret), uri: asText(data.uri) };
  }

  /** Confirm a code from the app: one-time codes are on, and the answer holds the recovery codes, shown once. */
  async totpConfirm(code: string): Promise<string[]> {
    return asTexts((await this.#call("POST", "/totp/confirm", { code })).recovery_codes);
  }

  /** A fresh set of recovery codes, replacing every old one. */
  async newRecoveryCodes(): Promise<string[]> {
    return asTexts((await this.#call("POST", "/totp/recovery-codes")).recovery_codes);
  }

  /** Switch one-time codes off: only with the password and a current code. */
  async totpDisable(password: string, code: string): Promise<void> {
    await this.#call("POST", "/totp/disable", { password, code });
  }

  async passkeys(): Promise<PasskeyInfo[]> {
    return asList((await this.#call("GET", "/passkeys")).data).map((p) => ({
      id: asText(p.id),
      name: asText(p.name),
      createdAt: asText(p.created_at),
      lastUsedAt: orNull(p.last_used_at),
    }));
  }

  /** WebAuthn's options for adding a passkey (lib/passkeys.ts turns them into what the browser takes). */
  async passkeyOptions(): Promise<Json> {
    return this.#call("POST", "/passkeys/options");
  }

  /** Keep a new passkey: the device's answer, with the password (and a current code, if one-time codes are on). */
  async addPasskey(
    name: string,
    answer: { client_data_json: string; attestation_object: string },
    password: string,
    code?: string,
  ): Promise<void> {
    const body: Json = { name, password, ...answer };
    if (code) body.code = code;
    await this.#call("POST", "/passkeys", body);
  }

  async removePasskey(id: string): Promise<void> {
    await this.#call("DELETE", `/passkeys/${encodeURIComponent(id)}`);
  }

  /** WebAuthn's options for signing in with a passkey, naming no account. */
  async passkeySignInOptions(): Promise<Json> {
    return this.#call("POST", "/passkey-login/options");
  }

  async passkeySignIn(answer: Json): Promise<Me> {
    return this.#remember(await this.#call("POST", "/passkey-login", answer));
  }

  async projects(org: string): Promise<Project[]> {
    const data = await this.#call("GET", `/orgs/${encodeURIComponent(org)}/projects`);
    return asList(data.data).map((p) => ({
      id: asText(p.id),
      name: asText(p.name),
      allowedOrigins: Array.isArray(p.allowed_origins) ? p.allowed_origins.map(asText) : [],
      retentionDays: typeof p.retention_days === "number" ? p.retention_days : 0,
    }));
  }

  async createKey(org: string, project: string, scopes: string[], livemode: boolean): Promise<NewKey> {
    const path = `/orgs/${encodeURIComponent(org)}/projects/${encodeURIComponent(project)}/keys`;
    const data = await this.#call("POST", path, { scopes, livemode });
    return {
      id: asText(data.id),
      key: asText(data.key),
      scopes: Array.isArray(data.scopes) ? data.scopes.map(asText) : [],
      livemode: data.livemode === true,
    };
  }

  async audit(org: string): Promise<AuditLog> {
    const data = await this.#call("GET", `/orgs/${encodeURIComponent(org)}/audit?limit=100`);
    const chain = asJson(data.chain);
    return {
      entries: asList(data.data).map((e) => ({
        seq: typeof e.seq === "number" ? e.seq : 0,
        actor: asText(e.actor),
        action: asText(e.action),
        target: asText(e.target),
        createdAt: asText(e.created_at),
      })),
      intact: chain.intact === true,
      firstBroken: typeof chain.first_broken === "number" ? chain.first_broken : null,
    };
  }

  #project(org: string, project: string): string {
    return `/orgs/${encodeURIComponent(org)}/projects/${encodeURIComponent(project)}`;
  }

  /** One page of a project's sessions, newest first; pass the last page's cursor for the next. */
  async sessions(
    org: string,
    project: string,
    livemode: boolean,
    after?: string,
    only: SessionSearch = {},
  ): Promise<SessionPage> {
    const query = new URLSearchParams({ livemode: String(livemode), limit: "20" });
    if (after) query.set("starting_after", after);
    if (only.outcome) query.set("outcome", only.outcome);
    if (only.externalRef) query.set("external_ref", only.externalRef);
    const data = await this.#call("GET", `${this.#project(org, project)}/sessions?${query}`);
    return { sessions: asList(data.data).map(asSession), nextCursor: orNull(data.next_cursor) };
  }

  async trace(org: string, project: string, session: string): Promise<SessionTrace> {
    const data = await this.#call(
      "GET",
      `${this.#project(org, project)}/sessions/${encodeURIComponent(session)}`,
    );
    const traced = asList(data.attempts).map((a) => ({
      kind: asText(a.kind),
      outcome: asText(a.outcome),
      reasons: asTexts(a.reasons),
      scores: asJson(a.scores),
      createdAt: asText(a.created_at),
    }));
    return { ...asSession(data), traced };
  }

  async analytics(org: string, project: string, livemode: boolean, days = 30): Promise<Analytics> {
    const query = new URLSearchParams({ livemode: String(livemode), days: String(days) });
    const data = await this.#call("GET", `${this.#project(org, project)}/analytics?${query}`);
    const totals: Record<string, number> = {};
    for (const [outcome, count] of Object.entries(asJson(data.totals))) totals[outcome] = asCount(count);
    const daily = asList(data.data).map((row) => ({
      day: asText(row.day),
      outcome: asText(row.outcome),
      sessions: asCount(row.sessions),
    }));
    const stage = asJson(data.face_stage);
    const outcomes: Record<string, number> = {};
    for (const [outcome, count] of Object.entries(asJson(stage.outcomes))) outcomes[outcome] = asCount(count);
    const median = stage.median_seconds === null ? null : asJson(stage.median_seconds);
    const faceStage = {
      decided: asCount(stage.decided),
      outcomes,
      median: median === null ? null : { from: asCount(median.from), to: orNumber(median.to) },
    };
    return { since: asText(data.since), totals, daily, faceStage };
  }

  /** The age model now deciding, or null when signed out. */
  async model(): Promise<ModelInfo | null> {
    let data: Json;
    try {
      data = await this.#call("GET", "/model");
    } catch (error) {
      if (error instanceof ConsoleError && error.status === 401) return null;
      throw error;
    }
    const training = data.training === null ? null : asJson(data.training);
    return {
      version: asText(data.version),
      calibrated: data.calibrated === true,
      note: orNull(data.note),
      permittedUse: orNull(data.permitted_use),
      backbone: training === null ? null : orNull(training.backbone),
      trainedOn: training === null ? null : asFaceSource(training.dataset, "name"),
      calibratedOn: asFaceSource(data.calibration, "dataset"),
      lines: asList(data.thresholds).map((t) => ({
        minAge: asCount(t.min_age),
        riskBudget: asCount(t.risk_budget),
        tauPass: asCount(t.tau_pass),
        tauFail: asCount(t.tau_fail),
        minorBound: orNumber(t.minor_bound),
        adultBound: orNumber(t.adult_bound),
        adults: asList(t.adults).map((band) => ({
          ages: asText(band.ages),
          faces: asCount(band.faces),
          pass: asCount(band.pass),
          stepUp: asCount(band.step_up),
          fail: asCount(band.fail),
        })),
      })),
    };
  }

  async policies(org: string, project: string): Promise<PolicyVersion[]> {
    const data = await this.#call("GET", `${this.#project(org, project)}/policies`);
    return asList(data.data).map((p) => ({
      id: asText(p.id),
      preset: p.preset === true,
      minAge: asCount(p.min_age),
      riskBudget: asCount(p.risk_budget),
      maxFaceAttempts: asCount(p.max_face_attempts),
      acceptAgePass: p.accept_age_pass === true,
    }));
  }

  async addPolicy(
    org: string,
    project: string,
    name: string,
    minAge: number,
    attempts: number,
    riskBudget: number,
    acceptAgePass = false,
  ): Promise<string> {
    const body = {
      name,
      min_age: minAge,
      max_face_attempts: attempts,
      risk_budget: riskBudget,
      accept_age_pass: acceptAgePass,
    };
    const data = await this.#call("POST", `${this.#project(org, project)}/policies`, body);
    return asText(data.id);
  }

  #hooks(org: string, project: string, endpoint?: string): string {
    const base = `${this.#project(org, project)}/webhooks`;
    return endpoint === undefined ? base : `${base}/${encodeURIComponent(endpoint)}`;
  }

  async webhooks(org: string, project: string, livemode: boolean): Promise<WebhookEndpoint[]> {
    const data = await this.#call("GET", `${this.#hooks(org, project)}?livemode=${livemode}`);
    return asList(data.data).map(asEndpoint);
  }

  async addWebhook(
    org: string,
    project: string,
    livemode: boolean,
    url: string,
    events: string[],
  ): Promise<NewWebhook> {
    const data = await this.#call("POST", this.#hooks(org, project), { url, events, livemode });
    return { ...asEndpoint(data), secret: asText(data.secret) };
  }

  async removeWebhook(org: string, project: string, livemode: boolean, endpoint: string): Promise<void> {
    await this.#call("DELETE", `${this.#hooks(org, project, endpoint)}?livemode=${livemode}`);
  }

  /** Switch an endpoint off (it keeps its address, events and secret, but gets nothing) or back on. */
  async switchWebhook(
    org: string,
    project: string,
    livemode: boolean,
    endpoint: string,
    enabled: boolean,
  ): Promise<WebhookEndpoint> {
    const path = `${this.#hooks(org, project, endpoint)}?livemode=${livemode}`;
    return asEndpoint(await this.#call("PATCH", path, { enabled }));
  }

  /** Queue a test event for one endpoint; returns the event's ID. */
  async testWebhook(org: string, project: string, livemode: boolean, endpoint: string): Promise<string> {
    const data = await this.#call("POST", `${this.#hooks(org, project, endpoint)}/test?livemode=${livemode}`);
    return asText(data.id);
  }

  async deliveries(org: string, project: string, livemode: boolean, endpoint: string): Promise<Delivery[]> {
    const data = await this.#call(
      "GET",
      `${this.#hooks(org, project, endpoint)}/deliveries?livemode=${livemode}`,
    );
    return asList(data.data).map((d) => ({
      id: asText(d.id),
      event: asText(d.event),
      status: asText(d.status),
      attempt: asCount(d.attempt),
      lastStatus: typeof d.last_status === "number" ? d.last_status : null,
      lastError: orNull(d.last_error),
      createdAt: asText(d.created_at),
    }));
  }

  /** Send a delivery again, from the start of the retry schedule. */
  async replay(org: string, project: string, livemode: boolean, delivery: string): Promise<void> {
    const path = `${this.#project(org, project)}/webhook-deliveries/${encodeURIComponent(delivery)}/replay`;
    await this.#call("POST", `${path}?livemode=${livemode}`);
  }
}
