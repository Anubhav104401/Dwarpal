import type { NextConfig } from "next";

const apiUrl = process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";
const development = process.env.NODE_ENV === "development";

const contentSecurityPolicy = [
  "default-src 'self'",
  `connect-src 'self' ${apiUrl}`,
  "img-src 'self' data: blob:",
  "media-src 'self' blob:",
  "font-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  // 'wasm-unsafe-eval' lets the browser compile WebAssembly (MediaPipe) — and only that: no eval of JavaScript.
  `script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'${development ? " 'unsafe-eval'" : ""}`,
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "Permissions-Policy", value: "camera=(self), microphone=(), geolocation=(), payment=()" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const config: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default config;
