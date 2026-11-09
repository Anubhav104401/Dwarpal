import { remoteKeys, verifyAgeToken } from "@dwarpal/node";
import { type NextRequest, NextResponse } from "next/server";

import { dwarpal, MIN_AGE, shopConfig } from "@/lib/config";
import { issuePass, PASS_COOKIE, PASS_LIFETIME_S, PENDING_COOKIE } from "@/lib/pass";

/**
 * Dwarpal sends the visitor back here with `?session_id=vs_…`. The shop never trusts that address alone: the
 * session must be the one this browser started, and the shop asks the API for the result with its secret key and
 * checks the signed token before letting anyone in.
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const config = shopConfig();
  const sessionId = request.nextUrl.searchParams.get("session_id") ?? "";
  const go = (path: string) => {
    const response = NextResponse.redirect(new URL(path, config.shopUrl), 303);
    response.cookies.delete({ name: PENDING_COOKIE, path: "/age-check" });
    return response;
  };
  if (sessionId === "" || request.cookies.get(PENDING_COOKIE)?.value !== sessionId) {
    return go("/refused?reason=other_browser");
  }
  try {
    const session = await dwarpal(config).retrieveSession(sessionId);
    if (session.status === "awaiting_step_up") {
      return go("/refused?reason=step_up");
    }
    if (session.status !== "completed" || session.ageToken === null) {
      return go("/refused?reason=unfinished");
    }
    const verdict = await verifyAgeToken(session.ageToken, {
      issuer: config.issuer,
      // The keys come from the address the shop reaches the API by — on the server, its private one — not from
      // the issuer's public address, which would mean leaving the server to come back to it.
      keys: remoteKeys(config.apiUrl),
      audience: config.projectId,
      minAge: MIN_AGE,
      sessionId,
    });
    if (!verdict.allowed) {
      return go("/refused?reason=not_confirmed");
    }
    const response = go("/cellar");
    response.cookies.set(PASS_COOKIE, issuePass(sessionId, config.secret), {
      httpOnly: true,
      sameSite: "lax",
      secure: config.shopUrl.startsWith("https://"),
      path: "/",
      maxAge: PASS_LIFETIME_S,
    });
    return response;
  } catch (error) {
    console.error("the age check could not be completed", error);
    return go("/refused?reason=error");
  }
}
