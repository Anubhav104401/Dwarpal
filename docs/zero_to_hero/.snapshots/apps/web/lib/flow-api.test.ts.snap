import { afterEach, describe, expect, it, vi } from "vitest";

import { FlowClient, FlowError } from "./flow-api";

const API = "http://localhost:8000";
const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";

function answer(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "x-request-id": "req_0123456789abcdef" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FlowClient", () => {
  it("starts with the secret, then sends the flow token with every later call", async () => {
    const seen: Request[] = [];
    const replies = [
      answer(200, {
        flow_token: "flow-token",
        session: {
          id: SESSION,
          status: "in_progress",
          outcome: null,
          project_name: "Amber Cellars",
          min_age: 18,
          attempts_remaining: 3,
        },
      }),
      answer(200, { challenge_id: "challenge-1", nonce: "n", poses: [], colours: [], expires_in: 120 }),
      answer(200, { outcome: "retry", reasons: ["too_dark"], attempts_remaining: 2 }),
    ];
    vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
      seen.push(new Request(input, init));
      return replies.shift() ?? answer(500, {});
    });
    const client = new FlowClient(`${API}/`, SESSION);
    const session = await client.start(`${SESSION}_secret_x`);
    const frame = { image: new Blob([new Uint8Array([255, 216, 255])], { type: "image/jpeg" }), tMs: 12.4 };
    const result = await client.attempt([frame, { ...frame, tMs: 160.2 }]);

    expect(session).toMatchObject({ projectName: "Amber Cellars", minAge: 18, attemptsRemaining: 3 });
    expect(seen.map((request) => new URL(request.url).pathname)).toEqual([
      `/v1/flow/sessions/${SESSION}/start`,
      `/v1/flow/sessions/${SESSION}/challenge`,
      `/v1/flow/sessions/${SESSION}/face-attempts`,
    ]);
    expect(seen[0]?.headers.get("authorization")).toBeNull();
    expect(seen[1]?.headers.get("authorization")).toBe("Bearer flow-token");
    const form = await seen[2]?.formData();
    expect(form?.get("challenge_id")).toBe("challenge-1");
    expect(JSON.parse(String(form?.get("meta")))).toEqual({
      frames: [
        { index: 0, t_ms: 12 },
        { index: 1, t_ms: 160 },
      ],
    });
    expect(form?.get("frame_1")).toBeInstanceOf(Blob);
    expect(result).toEqual({ outcome: "retry", reasons: ["too_dark"], attemptsRemaining: 2 });
  });

  it("turns refusals into FlowErrors with the code and the request ID", async () => {
    vi.stubGlobal("fetch", async () => answer(401, { code: "invalid_client_secret", detail: "no" }));
    const failure = await new FlowClient(API, SESSION).start("wrong").catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(FlowError);
    expect(failure).toMatchObject({
      status: 401,
      code: "invalid_client_secret",
      requestId: "req_0123456789abcdef",
    });
  });

  it("reports a lost connection as network_error", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("Failed to fetch");
    });
    await expect(new FlowClient(API, SESSION).finish()).rejects.toMatchObject({ code: "network_error" });
  });
});
