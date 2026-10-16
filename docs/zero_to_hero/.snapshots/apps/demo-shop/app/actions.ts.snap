"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { dwarpal, POLICY, shopConfig } from "@/lib/config";
import { PASS_LIFETIME_S, PENDING_COOKIE } from "@/lib/pass";

/** Ask Dwarpal for a verification session, then send the visitor to its verify page. */
export async function startAgeCheck(): Promise<void> {
  const config = shopConfig();
  const session = await dwarpal(config).createSession({
    policy: POLICY,
    returnUrl: `${config.shopUrl}/age-check/complete`,
  });
  (await cookies()).set(PENDING_COOKIE, session.id, {
    httpOnly: true,
    sameSite: "lax",
    secure: config.shopUrl.startsWith("https://"),
    path: "/age-check",
    maxAge: PASS_LIFETIME_S,
  });
  redirect(session.url);
}
