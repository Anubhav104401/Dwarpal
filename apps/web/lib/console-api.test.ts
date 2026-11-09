import { afterEach, describe, expect, it, vi } from "vitest";

import { CAN, ConsoleClient, ConsoleError, waitInWords } from "./console-api";

function answer(status: number, body: unknown): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const ME = {
  id: "usr_1",
  email: "ana@shop.example",
  totp_enabled: false,
  csrf_token: "csrf-from-me",
  organisations: [{ id: "org_1", name: "Shop Ltd", role: "owner" }],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ConsoleClient", () => {
  it("signs in, then repeats the CSRF token on every change and never on a read", async () => {
    const seen: Request[] = [];
    const replies = [answer(200, ME), answer(200, { object: "list", data: [] }), answer(201, {})];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push(new Request(new URL(url, "http://console.test"), init));
      return replies.shift();
    });
    const client = new ConsoleClient();
    const me = await client.signIn("ana@shop.example", "a long passphrase");
    await client.members("org_1");
    await client.addMember("org_1", "ben@shop.example", "analyst");

    expect(me.organisations).toEqual([{ id: "org_1", name: "Shop Ltd", role: "owner" }]);
    expect(seen.map((r) => [r.method, new URL(r.url).pathname])).toEqual([
      ["POST", "/console-api/login"],
      ["GET", "/console-api/orgs/org_1/members"],
      ["POST", "/console-api/orgs/org_1/members"],
    ]);
    expect(seen[1]?.headers.get("x-csrf-token")).toBeNull();
    expect(seen[2]?.headers.get("x-csrf-token")).toBe("csrf-from-me");
  });

  it("answers null for nobody signed in, and turns other refusals into ConsoleErrors", async () => {
    const replies = [
      answer(401, { code: "not_signed_in", detail: "sign in" }),
      answer(403, { code: "forbidden_for_role", detail: "your role (analyst) can't do this" }),
    ];
    vi.stubGlobal("fetch", async () => replies.shift());
    const client = new ConsoleClient();
    expect(await client.me()).toBeNull();
    const refused = client.createKey("org_1", "prj_1", ["sessions:read"], false);
    await expect(refused).rejects.toBeInstanceOf(ConsoleError);
    await expect(refused).rejects.toMatchObject({ status: 403, code: "forbidden_for_role" });
  });

  it("keeps how long a locked sign-in must wait, from Retry-After, and says it in words", async () => {
    const locked = new Response(JSON.stringify({ code: "too_many_sign_ins", detail: "wait" }), {
      status: 429,
      headers: { "content-type": "application/json", "retry-after": "240" },
    });
    const dated = new Response("{}", {
      status: 503,
      headers: { "retry-after": "Wed, 21 Oct 2026 07:28:00 GMT" },
    });
    const replies = [locked, dated];
    vi.stubGlobal("fetch", async () => replies.shift());
    const client = new ConsoleClient();
    await expect(client.signIn("ana@shop.example", "wrong")).rejects.toMatchObject({ retryAfter: 240 });
    await expect(client.signIn("ana@shop.example", "wrong")).rejects.toMatchObject({ retryAfter: null });
    expect([null, 0, 1, 45, 60, 61, 240, 3599, 3600, 7200].map(waitInWords)).toEqual([
      "in a moment",
      "in a moment",
      "in 1 second",
      "in 45 seconds",
      "in 1 minute",
      "in 2 minutes",
      "in 4 minutes",
      "in an hour",
      "in an hour",
      "in 2 hours",
    ]);
  });

  it("reads the audit log and its chain verdict", async () => {
    vi.stubGlobal("fetch", async () =>
      answer(200, {
        data: [
          { seq: 2, actor: "user:usr_1", action: "member.added", target: "usr_2", created_at: "2026-10-26" },
        ],
        chain: { entries: 2, intact: false, first_broken: 2 },
      }),
    );
    const log = await new ConsoleClient().audit("org_1");
    expect(log.entries[0]?.action).toBe("member.added");
    expect([log.intact, log.firstBroken]).toEqual([false, 2]);
  });
});

describe("ConsoleClient, a project's pages", () => {
  it("asks for sessions by mode and cursor, and reads a trace's attempts and scores", async () => {
    const seen: string[] = [];
    const replies = [
      answer(200, {
        data: [{ id: "vs_1", status: "completed", outcome: "pass", policy: "uk_osa_18", attempts: 1 }],
        next_cursor: "vs_1",
      }),
      answer(200, {
        id: "vs_1",
        status: "completed",
        outcome: "pass",
        policy: "uk_osa_18",
        attempts: [{ kind: "face", outcome: "pass", reasons: [], scores: { p_over: 0.99, tau: 0.9 } }],
      }),
      answer(200, {
        since: "2026-09-27",
        data: [{ day: "2026-10-01", policy: "uk_osa_18", outcome: "pass", sessions: 3 }],
        totals: { pass: 3, step_up: 1 },
        face_stage: {
          decided: 5,
          outcomes: { pass: 4, step_up: 1 },
          median_seconds: { from: 300, to: null },
        },
        document_stage: { opened: 4, outcomes: { pass: 2, fail: 1 } },
      }),
    ];
    vi.stubGlobal("fetch", async (url: string) => {
      seen.push(url);
      return replies.shift();
    });
    const client = new ConsoleClient();
    const page = await client.sessions("org_1", "prj_1", true, "vs_9");
    const trace = await client.trace("org_1", "prj_1", "vs_1");
    const counts = await client.analytics("org_1", "prj_1", false);

    expect(seen[0]).toBe(
      "/console-api/orgs/org_1/projects/prj_1/sessions?livemode=true&limit=20&starting_after=vs_9",
    );
    expect([page.sessions[0]?.outcome, page.nextCursor]).toEqual(["pass", "vs_1"]);
    expect(trace.traced[0]?.scores).toEqual({ p_over: 0.99, tau: 0.9 });
    expect(counts.totals).toEqual({ pass: 3, step_up: 1 });
    expect(counts.daily).toEqual([{ day: "2026-10-01", outcome: "pass", sessions: 3 }]);
    expect(counts.faceStage).toEqual({
      decided: 5,
      outcomes: { pass: 4, step_up: 1 },
      median: { from: 300, to: null },
    });
    expect(counts.documentStage).toEqual({ opened: 4, outcomes: { pass: 2, fail: 1 } });
  });
});

describe("ConsoleClient, webhooks", () => {
  it("sends the mode with every webhook request, and keeps the new endpoint's secret", async () => {
    const seen: Array<[string, string, string | null]> = [];
    const replies = [
      answer(200, { csrf_token: "c1", organisations: [] }),
      answer(201, {
        id: "whe_1",
        url: "https://shop.example/hooks",
        events: ["verification_session.completed"],
        secret: "whsec_x",
      }),
      answer(200, { data: [{ id: "whd_1", event: "evt_1", status: "dead", attempt: 8, last_status: 500 }] }),
      answer(204, {}),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push([init.method ?? "GET", url, typeof init.body === "string" ? init.body : null]);
      return replies.shift();
    });
    const client = new ConsoleClient();
    await client.me();
    const created = await client.addWebhook("org_1", "prj_1", true, "https://shop.example/hooks", [
      "verification_session.completed",
    ]);
    const deliveries = await client.deliveries("org_1", "prj_1", true, "whe_1");
    await client.removeWebhook("org_1", "prj_1", true, "whe_1");

    expect(created.secret).toBe("whsec_x");
    expect(JSON.parse(seen[1]?.[2] ?? "{}")).toEqual({
      url: "https://shop.example/hooks",
      events: ["verification_session.completed"],
      livemode: true,
    });
    expect(seen[2]?.[1]).toBe(
      "/console-api/orgs/org_1/projects/prj_1/webhooks/whe_1/deliveries?livemode=true",
    );
    expect([deliveries[0]?.status, deliveries[0]?.lastStatus, deliveries[0]?.lastError]).toEqual([
      "dead",
      500,
      null,
    ]);
    expect(seen[3]?.slice(0, 2)).toEqual([
      "DELETE",
      "/console-api/orgs/org_1/projects/prj_1/webhooks/whe_1?livemode=true",
    ]);
  });
});

describe("ConsoleClient, searching sessions", () => {
  it("adds only the filters that are set to the address", async () => {
    const seen: string[] = [];
    vi.stubGlobal("fetch", async (url: string) => {
      seen.push(url);
      return answer(200, { data: [], next_cursor: null });
    });
    const client = new ConsoleClient();
    await client.sessions("org_1", "prj_1", false, undefined, { outcome: "pass", externalRef: "order 7" });
    await client.sessions("org_1", "prj_1", false, undefined, { outcome: "" });

    expect(seen[0]).toBe(
      "/console-api/orgs/org_1/projects/prj_1/sessions?livemode=false&limit=20&outcome=pass&external_ref=order+7",
    );
    expect(seen[1]).toBe("/console-api/orgs/org_1/projects/prj_1/sessions?livemode=false&limit=20");
  });
});

describe("ConsoleClient, switching a webhook", () => {
  it("sends PATCH with the new state and the mode, and reads the endpoint back", async () => {
    const seen: Array<[string, string, string | null]> = [];
    const replies = [
      answer(200, { csrf_token: "c1", organisations: [] }),
      answer(200, { id: "whe_1", url: "https://shop.example/hooks", events: [], enabled: false }),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push([init.method ?? "GET", url, typeof init.body === "string" ? init.body : null]);
      return replies.shift();
    });
    const client = new ConsoleClient();
    await client.me();
    const endpoint = await client.switchWebhook("org_1", "prj_1", false, "whe_1", false);

    expect(seen[1]).toEqual([
      "PATCH",
      "/console-api/orgs/org_1/projects/prj_1/webhooks/whe_1?livemode=false",
      '{"enabled":false}',
    ]);
    expect(endpoint.enabled).toBe(false);
  });
});

describe("ConsoleClient, members and one-time codes", () => {
  it("changes and removes members by their IDs, and confirms a code", async () => {
    const seen: Array<[string, string, string | null]> = [];
    const replies = [
      answer(200, { csrf_token: "c1", organisations: [] }),
      answer(200, { user: "usr_2", role: "admin" }),
      answer(204, {}),
      answer(200, { secret: "JBSWY3DPEHPK3PXP", uri: "otpauth://totp/Dwarpal:a" }),
      answer(200, { recovery_codes: ["abcde-fghij", "klmno-pqrst"] }),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push([init.method ?? "GET", url, typeof init.body === "string" ? init.body : null]);
      return replies.shift();
    });
    const client = new ConsoleClient();
    await client.me();
    await client.changeRole("org_1", "usr_2", "admin");
    await client.removeMember("org_1", "usr_2");
    const offer = await client.totpEnrol();
    const codes = await client.totpConfirm("123456");

    expect(seen.slice(1).map(([method, url]) => `${method} ${url}`)).toEqual([
      "PATCH /console-api/orgs/org_1/members/usr_2",
      "DELETE /console-api/orgs/org_1/members/usr_2",
      "POST /console-api/totp",
      "POST /console-api/totp/confirm",
    ]);
    expect(seen[1]?.[2]).toBe('{"role":"admin"}');
    expect(offer.secret).toBe("JBSWY3DPEHPK3PXP");
    expect(seen[4]?.[2]).toBe('{"code":"123456"}');
    expect(codes).toEqual(["abcde-fghij", "klmno-pqrst"]); // the recovery codes, shown once
  });
});

describe("ConsoleClient, policies", () => {
  it("reads whether a policy version accepts Age Passes, and can add one that does (Phase 9)", async () => {
    const seen: Request[] = [];
    const policy = { id: "pass_18@1", preset: false, min_age: 18, risk_budget: 0.02, max_face_attempts: 3 };
    const replies = [
      answer(200, {
        object: "list",
        data: [
          { ...policy, accept_age_pass: true },
          { ...policy, id: "uk_osa_18" },
        ],
      }),
      answer(201, { id: "pass_18@2" }),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push(new Request(new URL(url, "http://console.test"), init));
      return replies.shift();
    });
    const client = new ConsoleClient();
    const listed = await client.policies("org_1", "prj_1");
    const added = await client.addPolicy("org_1", "prj_1", "pass_18", 18, 3, 0.02, true);

    expect(listed.map((p) => [p.id, p.acceptAgePass])).toEqual([
      ["pass_18@1", true],
      ["uk_osa_18", false],
    ]);
    expect(added).toBe("pass_18@2");
    expect(await seen[1]?.json()).toEqual({
      name: "pass_18",
      min_age: 18,
      max_face_attempts: 3,
      risk_budget: 0.02,
      accept_age_pass: true,
    });
  });
});

describe("ConsoleClient, projects and keys", () => {
  it("makes and changes projects, lists keys without secrets and stops one (D28-D30)", async () => {
    const seen: Array<[string, string, string | null]> = [];
    const project = {
      id: "prj_2",
      name: "Shop",
      allowed_origins: ["https://shop.example"],
      retention_days: 90,
    };
    const replies = [
      answer(200, { csrf_token: "c1", organisations: [] }),
      answer(201, project),
      answer(200, { ...project, name: "Cellar shop" }),
      answer(200, {
        object: "list",
        data: [
          { id: "dk_b", livemode: false, scopes: ["sessions:read"], created_at: "2026-11-08T20:00:00+00:00" },
          {
            id: "dk_a",
            livemode: true,
            scopes: [],
            state: "revoked",
            revoked_at: "2026-11-08T21:00:00+00:00",
          },
        ],
      }),
      answer(204, {}),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      seen.push([init.method ?? "GET", url, typeof init.body === "string" ? init.body : null]);
      return replies.shift();
    });
    const client = new ConsoleClient();
    await client.me();
    const made = await client.createProject("org_1", "Shop", ["https://shop.example"]);
    const renamed = await client.updateProject("org_1", "prj_2", { name: "Cellar shop" });
    const keys = await client.keys("org_1", "prj_2");
    await client.revokeKey("org_1", "prj_2", "dk_b");

    expect(seen.slice(1).map(([method, url, body]) => `${method} ${url} ${body ?? ""}`.trim())).toEqual([
      'POST /console-api/orgs/org_1/projects {"name":"Shop","allowed_origins":["https://shop.example"]}',
      'PATCH /console-api/orgs/org_1/projects/prj_2 {"name":"Cellar shop"}', // only what changes is sent
      "GET /console-api/orgs/org_1/projects/prj_2/keys",
      "DELETE /console-api/orgs/org_1/projects/prj_2/keys/dk_b",
    ]);
    expect(made).toEqual({
      id: "prj_2",
      name: "Shop",
      allowedOrigins: ["https://shop.example"],
      retentionDays: 90,
    });
    expect(renamed.name).toBe("Cellar shop");
    expect(keys.map((k) => [k.id, k.state, k.livemode, k.revokedAt])).toEqual([
      ["dk_b", "active", false, null], // a state the API didn't send reads as active
      ["dk_a", "revoked", true, "2026-11-08T21:00:00+00:00"],
    ]);
  });
});

describe("ConsoleClient, invitations and the account", () => {
  it("invites, lists and cancels; changes the password with a new CSRF token; deletes the account (D31, D32, D44)", async () => {
    const seen: Array<[string, string | null, string | null]> = [];
    const replies = [
      answer(200, { csrf_token: "c1", organisations: [] }),
      answer(201, { invitation: "inv_1", email: "new@shop.example", role: "developer", pending: true }),
      answer(200, {
        data: [
          { id: "inv_1", email: "new@shop.example", role: "developer", created_at: "2026-11-08T22:00:00Z" },
        ],
      }),
      answer(204, {}),
      answer(200, { csrf_token: "c2", organisations: [] }),
      answer(204, {}),
    ];
    vi.stubGlobal("fetch", async (url: string, init: RequestInit) => {
      const headers = new Headers(init.headers);
      seen.push([
        `${init.method ?? "GET"} ${url}`,
        typeof init.body === "string" ? init.body : null,
        headers.get("X-CSRF-Token"),
      ]);
      return replies.shift();
    });
    const client = new ConsoleClient();
    await client.me();
    const added = await client.addMember("org_1", "new@shop.example", "developer");
    const waiting = await client.invitations("org_1");
    await client.cancelInvitation("org_1", "inv_1");
    await client.changePassword("old password!", "a new long passphrase", "123456");
    await client.deleteAccount("a new long passphrase");

    expect(added).toEqual({ pending: true });
    expect(waiting).toEqual([
      { id: "inv_1", email: "new@shop.example", role: "developer", createdAt: "2026-11-08T22:00:00Z" },
    ]);
    expect(seen.slice(1).map(([call]) => call)).toEqual([
      "POST /console-api/orgs/org_1/members",
      "GET /console-api/orgs/org_1/invitations",
      "DELETE /console-api/orgs/org_1/invitations/inv_1",
      "POST /console-api/password",
      "POST /console-api/account/delete",
    ]);
    expect(seen[4]?.[1]).toBe(
      '{"password":"old password!","new_password":"a new long passphrase","code":"123456"}',
    );
    expect(seen[5]?.[2]).toBe("c2"); // the new session's token, from the password change
    expect(seen[5]?.[1]).toBe('{"password":"a new long passphrase"}'); // no code when none is given
  });
});

describe("CAN", () => {
  it("mirrors the API's role matrix for what the pages offer", () => {
    expect(["owner", "admin", "developer", "analyst"].map((r) => CAN.manageKeys(r as never))).toEqual([
      true,
      true,
      true,
      false,
    ]);
    expect(CAN.manageMembers("developer")).toBe(false);
    expect(CAN.readAudit("admin")).toBe(true);
    expect(["owner", "admin", "developer", "analyst"].map((r) => CAN.manageProjects(r as never))).toEqual([
      true,
      true,
      false,
      false,
    ]);
  });
});

describe("ConsoleClient, the model page", () => {
  it("reads the model's sources and lines, keeps a missing bound as unknown, and is null when signed out", async () => {
    const replies = [
      answer(200, {
        version: "age-1",
        calibrated: false,
        note: "Test mode only.",
        permitted_use: "research",
        training: {
          backbone: "convnext",
          dataset: { name: "fairface", licence: "CC BY 4.0", age_source: "guessed" },
        },
        calibration: { dataset: "utkface", licence: "research", age_source: "checked", faces: 11301 },
        thresholds: [
          {
            min_age: 18,
            risk_budget: 0.075,
            tau_pass: 0.96,
            tau_fail: 0.38,
            minor_bound: 0.07,
            adult_bound: null,
            adults: [{ ages: "18-20", faces: 330, pass: 0.1333, step_up: 0.7727, fail: 0.0939 }],
          },
        ],
      }),
      answer(401, { code: "not_signed_in", detail: "sign in" }),
    ];
    vi.stubGlobal("fetch", async () => replies.shift());
    const client = new ConsoleClient();

    const model = await client.model();

    expect(model?.trainedOn).toEqual({
      name: "fairface",
      licence: "CC BY 4.0",
      ageSource: "guessed",
      faces: null,
    });
    expect(model?.calibratedOn?.faces).toBe(11301);
    expect(model?.lines[0]).toEqual({
      minAge: 18,
      riskBudget: 0.075,
      tauPass: 0.96,
      tauFail: 0.38,
      minorBound: 0.07,
      adultBound: null,
      adults: [{ ages: "18-20", faces: 330, pass: 0.1333, stepUp: 0.7727, fail: 0.0939 }],
    });
    expect(await client.model()).toBeNull();
  });
});
