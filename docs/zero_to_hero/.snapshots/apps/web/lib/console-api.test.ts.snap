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
      answer(200, { since: "2026-09-27", totals: { pass: 3, step_up: 1 } }),
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
