/**
 * The languages of the public pages: English and Hindi (decision D2), and since 14 Nov 2026 eight more of India's
 * major languages — Bengali, Marathi, Telugu, Tamil, Gujarati, Kannada, Malayalam and Punjabi. Each is its ISO 639-1
 * code, which is also what browsers send in `Accept-Language`. The console stays in English.
 */
export const LOCALES = ["en", "hi", "bn", "mr", "te", "ta", "gu", "kn", "ml", "pa"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";
/** The cookie that remembers a person's own choice: next-intl's usual name for it. */
export const LOCALE_COOKIE = "NEXT_LOCALE";

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

/**
 * The language to answer in: the person's own choice, if they made one; otherwise the first of their browser's
 * languages (its `Accept-Language` header, most wanted first) that the pages are written in; otherwise English.
 */
export function pickLocale(choice: string | undefined, acceptLanguage: string | null): Locale {
  if (isLocale(choice)) {
    return choice;
  }
  const wanted = (acceptLanguage ?? "")
    .split(",")
    .map((part, order) => {
      const [tag = "", ...params] = part.trim().split(";");
      const weight = params.map((p) => p.trim()).find((p) => p.startsWith("q="));
      const quality = weight === undefined ? 1 : Number(weight.slice(2));
      return {
        language: tag.toLowerCase().split("-")[0],
        quality: Number.isNaN(quality) ? 0 : quality,
        order,
      };
    })
    .filter((entry) => entry.quality > 0)
    .sort((a, b) => b.quality - a.quality || a.order - b.order);
  return wanted.map((entry) => entry.language).find(isLocale) ?? DEFAULT_LOCALE;
}
