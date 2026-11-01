import { useLocale, useTranslations } from "next-intl";

import { chooseLocale } from "@/i18n/actions";
import { LOCALES } from "@/i18n/locales";

import { button } from "./ui";

/** English or Hindi: each name written in its own language and script, so a person can find theirs. */
export function LanguageSwitch() {
  const locale = useLocale();
  const t = useTranslations("Language");
  return (
    <form action={chooseLocale} className="flex gap-0.5" aria-label={t("label")}>
      {LOCALES.map((option) => (
        <button
          key={option}
          type="submit"
          name="locale"
          value={option}
          lang={option}
          aria-pressed={option === locale}
          className={`${button("quiet", "compact")} aria-pressed:bg-ink-200/70 aria-pressed:text-ink-900 dark:aria-pressed:bg-white/15 dark:aria-pressed:text-white`}
        >
          {t(option)}
        </button>
      ))}
    </form>
  );
}
