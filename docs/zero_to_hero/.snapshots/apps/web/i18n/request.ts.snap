import { cookies, headers } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { LOCALE_COOKIE, pickLocale } from "./locales";

/** For each request: the language (`pickLocale`) and its words, read by next-intl wherever a page asks for them. */
export default getRequestConfig(async () => {
  const choice = (await cookies()).get(LOCALE_COOKIE)?.value;
  const locale = pickLocale(choice, (await headers()).get("accept-language"));
  return { locale, messages: (await import(`../messages/${locale}.json`)).default };
});
