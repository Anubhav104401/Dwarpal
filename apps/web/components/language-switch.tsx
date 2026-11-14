import { useLocale, useTranslations } from "next-intl";

import { chooseLocale } from "@/i18n/actions";
import { LOCALES } from "@/i18n/locales";

import { button } from "./ui";

/**
 * The language menu: the current language's name, which opens a list of all ten, each written in its own language
 * and script so a person can find theirs. `<details>` opens and closes without any script, and each choice is a plain
 * form button, so the menu works before JavaScript loads, or without it.
 */
export function LanguageSwitch() {
  const locale = useLocale();
  const t = useTranslations("Language");
  return (
    // Keyed by the language, so the menu is drawn afresh — closed — once a choice has changed it.
    <details key={locale} className="group relative">
      <summary
        className={`${button("quiet", "compact")} cursor-pointer list-none [&::-webkit-details-marker]:hidden`}
        aria-label={`${t("label")}: ${t(locale)}`}
      >
        <span lang={locale}>{t(locale)}</span>
        <span aria-hidden="true" className="ml-1 text-xs transition-transform group-open:rotate-180">
          ▾
        </span>
      </summary>
      <form
        action={chooseLocale}
        aria-label={t("label")}
        className="absolute right-0 z-20 mt-1 grid w-44 gap-0.5 rounded-xl border border-ink-200 bg-white p-1 shadow-lg dark:border-white/10 dark:bg-ink-900"
      >
        {LOCALES.map((option) => (
          <button
            key={option}
            type="submit"
            name="locale"
            value={option}
            lang={option}
            aria-pressed={option === locale}
            className={`${button("quiet", "compact")} justify-start aria-pressed:bg-ink-200/70 aria-pressed:text-ink-900 dark:aria-pressed:bg-white/15 dark:aria-pressed:text-white`}
          >
            {t(option)}
          </button>
        ))}
      </form>
    </details>
  );
}
