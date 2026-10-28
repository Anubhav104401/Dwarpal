import { type NextRequest, NextResponse } from "next/server";

/*
 * The content security policy, made afresh for every page (Phase 7): a random **nonce** each time, and only scripts
 * carrying it may run. Next.js puts the nonce on its own scripts while it renders the page; a script that a trusted
 * one adds (MediaPipe's WebAssembly loader) is trusted too ('strict-dynamic'). An injected script can't know the
 * nonce, so it doesn't run — which 'unsafe-inline', the policy's earlier setting, couldn't promise (ZAP's finding).
 */

const apiUrl = process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";
const development = process.env.NODE_ENV === "development";

export function policy(nonce: string): string {
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
    "frame-ancestors 'none'",
  ].join("; ");
}

export function proxy(request: NextRequest): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const header = policy(nonce);
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
