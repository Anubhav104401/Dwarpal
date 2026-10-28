import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { policy, proxy } from "./proxy";

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

  it("gives every page a fresh nonce, in the answer and in the request Next.js renders", () => {
    const first = proxy(new NextRequest("http://localhost:3000/console"));
    const second = proxy(new NextRequest("http://localhost:3000/console"));
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
