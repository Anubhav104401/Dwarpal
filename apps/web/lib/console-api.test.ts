import { afterEach, describe, expect, it, vi } from "vitest";

import { CAN, ConsoleClient, ConsoleError } from "./console-api";

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
  });
});
