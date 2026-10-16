import { describe, expect, it } from "vitest";

import { DwarpalApiError, DwarpalClient } from "../src/index.js";

const KEY = "dk_test_abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG";
const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";

function fakeFetch(status: number, body: unknown, seen: Request[] = []): typeof fetch {
  return async (input, init) => {
    seen.push(new Request(input, init));
    const headers = { "content-type": "application/json", "x-request-id": "req_0123456789abcdef" };
    return new Response(JSON.stringify(body), { status, headers });
  };
}

describe("DwarpalClient", () => {
  it("creates a session with the secret key, and translates the answer", async () => {
    const seen: Request[] = [];
    const answer = {
      id: SESSION,
      object: "verification_session",
      status: "created",
      livemode: false,
      policy: "uk_osa_18",
      client_secret: `${SESSION}_secret_x`,
      url: `http://localhost:3000/v/${SESSION}#cs=${SESSION}_secret_x`,
      expires_at: "2026-10-16T12:00:00+00:00",
    };
    const client = new DwarpalClient({
      apiKey: KEY,
      baseUrl: "http://localhost:8000/",
      fetch: fakeFetch(201, answer, seen),
    });
    const created = await client.createSession({
      policy: "uk_osa_18",
      returnUrl: "http://localhost:3100/done",
    });
    const [request] = seen;
    expect(request?.url).toBe("http://localhost:8000/v1/verification-sessions");
    expect(request?.headers.get("authorization")).toBe(`Bearer ${KEY}`);
    expect(await request?.json()).toEqual({ policy: "uk_osa_18", return_url: "http://localhost:3100/done" });
    expect(created.url).toBe(answer.url);
    expect(created.expiresAt.toISOString()).toBe("2026-10-16T12:00:00.000Z");
    expect(created).not.toHaveProperty("client_secret");
  });

  it("reads a completed session with its token", async () => {
    const answer = {
      id: SESSION,
      status: "completed",
      outcome: "pass",
      livemode: false,
      policy: "uk_osa_18",
      min_age: 18,
      attempts: 1,
      external_ref: null,
      completed_at: "2026-10-16T12:00:00+00:00",
      age_token: "header.claims.signature",
    };
    const client = new DwarpalClient({
      apiKey: KEY,
      baseUrl: "http://localhost:8000",
      fetch: fakeFetch(200, answer),
    });
    const result = await client.retrieveSession(SESSION);
    expect(result.outcome).toBe("pass");
    expect(result.minAge).toBe(18);
    expect(result.completedAt?.toISOString()).toBe("2026-10-16T12:00:00.000Z");
    expect(result.ageToken).toBe("header.claims.signature");
  });

  it("turns problem details into errors that carry the code and the request ID", async () => {
    const problem = { status: 401, code: "invalid_api_key", detail: "this API key is unknown or revoked" };
    const client = new DwarpalClient({
      apiKey: KEY,
      baseUrl: "http://localhost:8000",
      fetch: fakeFetch(401, problem),
    });
    const failure = await client.createSession().catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(DwarpalApiError);
    expect(failure).toMatchObject({
      status: 401,
      code: "invalid_api_key",
      requestId: "req_0123456789abcdef",
    });
  });

  it("refuses malformed keys and session IDs before sending anything", async () => {
    const seen: Request[] = [];
    expect(() => new DwarpalClient({ apiKey: "sk_live_wrong", baseUrl: "http://localhost:8000" })).toThrow(
      TypeError,
    );
    const client = new DwarpalClient({
      apiKey: KEY,
      baseUrl: "http://localhost:8000",
      fetch: fakeFetch(200, {}, seen),
    });
    await expect(client.retrieveSession("vs_short")).rejects.toThrow(TypeError);
    expect(seen).toHaveLength(0);
  });
});
