"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { dwarpal, POLICY, shopConfig } from "@/lib/config";
import { PASS_COOKIE, PASS_LIFETIME_S, PENDING_COOKIE } from "@/lib/pass";

/** Ask Dwarpal for a verification session, remember it in this browser, and hand its verify link to the page,
 * which opens it with Dwarpal's browser SDK. */
export async function createAgeCheck(): Promise<string> {
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
  return session.url;
}

/** Forget this browser's pass and go back to the front door: the next visit to the cellar needs a new age check. */
export async function leaveCellar(): Promise<void> {
  (await cookies()).delete(PASS_COOKIE);
  redirect("/");
}
