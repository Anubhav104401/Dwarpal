"use server";

import { cookies } from "next/headers";

import { isLocale, LOCALE_COOKIE } from "./locales";

/** Remember the language a person chose, for a year. A plain form posts here, so it works without JavaScript too;
 * Next.js then draws the page again in that language. Anything that isn't one of the pages' languages is ignored. */
export async function chooseLocale(form: FormData): Promise<void> {
  const locale = form.get("locale");
  if (isLocale(locale)) {
    (await cookies()).set(LOCALE_COOKIE, locale, { path: "/", maxAge: 365 * 24 * 3600, sameSite: "lax" });
  }
}
