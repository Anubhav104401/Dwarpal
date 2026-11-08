import { type NextRequest, NextResponse } from "next/server";

/*
 * The content security policy, made afresh for every page (Phase 7): a random **nonce** each time, and only scripts
 * carrying it may run. Next.js puts the nonce on its own scripts while it renders the page; a script that a trusted
 * one adds (MediaPipe's WebAssembly loader) is trusted too ('strict-dynamic'). An injected script can't know the
 * nonce, so it doesn't run — which 'unsafe-inline', the policy's earlier setting, couldn't promise (ZAP's finding).
 */

const apiUrl = process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";
// How this server reaches the API, if not by the public address (inside a private network, say).
const internalApiUrl = process.env.DWARPAL_API_INTERNAL_URL ?? apiUrl;
const development = process.env.NODE_ENV === "development";

const VERIFY_PAGE = /^\/v\/(vs_[0-9A-Za-z]{26})$/;
// An origin and nothing else — scheme, host, optional port — before it goes into a header.
const ORIGIN = /^https?:\/\/[A-Za-z0-9.-]+(:\d{1,5})?$/;

/**
 * Which website may show this verify page inside a frame (decision D16): the one its session will send the person
 * back to, as the API says. Any doubt — another page, an API that is slow or down, a strange answer — means none.
 * `forwardedFor` is the visitor's address as Caddy gave it: the API limits the verify page's calls per address, so
 * the lookup is counted against the visitor, not against this server, which asks for every visitor.
 */
export async function frameAncestorFor(
  path: string,
  ask: typeof fetch,
  forwardedFor: string | null = null,
): Promise<string | null> {
  const session = VERIFY_PAGE.exec(path)?.[1];
  if (session === undefined) {
    return null;
  }
  try {
    const answer = await ask(`${internalApiUrl}/v1/flow/sessions/${session}/frame-ancestor`, {
      signal: AbortSignal.timeout(1500),
      cache: "no-store",
      headers: forwardedFor === null ? {} : { "X-Forwarded-For": forwardedFor },
    });
    const origin: unknown = answer.ok ? ((await answer.json()) as { origin?: unknown }).origin : null;
    return typeof origin === "string" && ORIGIN.test(origin) ? origin : null;
  } catch {
    return null;
  }
}

export function policy(nonce: string, frameAncestor: string | null = null): string {
  return [
    "default-src 'self'",
    `connect-src 'self' ${apiUrl}`,
    "img-src 'self' data: blob:",
    "media-src 'self' blob:",
    "font-src 'self'",
    // Styles stay open to inline ones: a few elements set their colour or width in a style attribute, which a nonce
    // can't cover; injected styles can't run code.
    "style-src 'self' 'unsafe-inline'",
    // 'wasm-unsafe-eval' lets the browser compile WebAssembly (MediaPipe) — and only that: no eval of JavaScript.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'wasm-unsafe-eval'${development ? " 'unsafe-eval'" : ""}`,
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    `frame-ancestors ${frameAncestor ?? "'none'"}`,
  ].join("; ");
}

export function proxy(request: NextRequest): Promise<NextResponse> {
  return secure(request, fetch);
}

/** The page's answer with its policy; `ask` is how the API is asked (a stand-in, in tests). */
export async function secure(request: NextRequest, ask: typeof fetch): Promise<NextResponse> {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const visitor = request.headers.get("x-forwarded-for");
  const header = policy(nonce, await frameAncestorFor(request.nextUrl.pathname, ask, visitor));
  // Next.js reads the policy from the request to find the nonce; the browser reads it from the response.
  const headers = new Headers(request.headers);
  headers.set("Content-Security-Policy", header);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", header);
  return response;
}

export const config = {
  // Pages only: not the built files (they are never pages), the API passage, or link prefetches.
  matcher: [
    {
      source: "/((?!_next/static|_next/image|console-api|mediapipe|favicon.ico).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
