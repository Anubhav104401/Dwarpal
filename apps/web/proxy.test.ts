import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { frameAncestorFor, policy, proxy, secure } from "./proxy";

const SESSION = "vs_01M51KF05CE4GSBH7F0G43G01V";

/** A stand-in for the API: answers every request with `body` (as JSON) and `status`, and notes what was asked. */
function api(status: number, body: unknown, asked: string[] = []): typeof fetch {
  return async (input) => {
    asked.push(String(input));
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  };
}

const ancestors = (header: string | null) =>
  (header ?? "").split("; ").find((part) => part.startsWith("frame-ancestors"));

describe("the content security policy", () => {
  it("lets only scripts with this page's nonce run, never inline ones", () => {
    const scripts =
      policy("abc123")
        .split("; ")
        .find((part) => part.startsWith("script-src")) ?? "";
    expect(scripts).toContain("'nonce-abc123'");
    expect(scripts).toContain("'strict-dynamic'");
    expect(scripts).not.toContain("'unsafe-inline'");
  });

  it("gives every page a fresh nonce, in the answer and in the request Next.js renders", async () => {
    const first = await proxy(new NextRequest("http://localhost:3000/console"));
    const second = await proxy(new NextRequest("http://localhost:3000/console"));
    const nonce = (header: string | null) => /'nonce-([^']+)'/.exec(header ?? "")?.[1];
    expect(nonce(first.headers.get("content-security-policy"))).toBeTruthy();
    expect(nonce(first.headers.get("content-security-policy"))).not.toBe(
      nonce(second.headers.get("content-security-policy")),
    );
    // NextResponse.next passes the changed request headers on as "x-middleware-request-*" headers.
    expect(first.headers.get("x-middleware-request-content-security-policy")).toBe(
      first.headers.get("content-security-policy"),
    );
  });
});

describe("framing (decision D16)", () => {
  it("lets the session's own website frame its verify page, and no other page", async () => {
    const asked: string[] = [];
    const verify = await secure(
      new NextRequest(`http://localhost:3000/v/${SESSION}`),
      api(200, { origin: "https://shop.example" }, asked),
    );
    const elsewhere = await secure(
      new NextRequest("http://localhost:3000/console"),
      api(200, { origin: "https://shop.example" }, asked),
    );
    expect(ancestors(verify.headers.get("content-security-policy"))).toBe(
      "frame-ancestors https://shop.example",
    );
    expect(ancestors(elsewhere.headers.get("content-security-policy"))).toBe("frame-ancestors 'none'");
    expect(asked).toEqual([`http://localhost:8000/v1/flow/sessions/${SESSION}/frame-ancestor`]);
  });

  it.each([
    ["no website for the session", api(200, { origin: null })],
    ["an API error", api(503, { origin: "https://shop.example" })],
    ["something that isn't an origin", api(200, { origin: "https://shop.example; script-src *" })],
    ["an address with a path", api(200, { origin: "https://shop.example/age" })],
    [
      "an API that can't be reached",
      (async () => Promise.reject(new TypeError("fetch failed"))) as typeof fetch,
    ],
  ])("lets no one frame it on %s", async (_, ask) => {
    expect(await frameAncestorFor(`/v/${SESSION}`, ask)).toBeNull();
  });
});
