import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const apiUrl = process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000";
// The content security policy is made per request, with a nonce (proxy.ts); these are the same for every answer.
const securityHeaders = [
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
  // The console calls the API through this site, so its session cookie belongs to one origin (as Caddy does it in
  // production, where both are served from one address).
  async rewrites() {
    return [{ source: "/console-api/:path*", destination: `${apiUrl}/console/v1/:path*` }];
  },
};

// The public pages speak English and Hindi (decision D2): next-intl reads each request's language and words here.
export default createNextIntlPlugin("./i18n/request.ts")(config);
