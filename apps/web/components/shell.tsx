import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { LanguageSwitch } from "./language-switch";

import { Badge, button } from "./ui";

// The verify page's pieces, from the design system.
export { card } from "./ui";
export const primaryButton = button("primary", "large");
export const accentButton = button("accent", "large");
export const quietButton = button("quiet", "large");

/** Dwarpal's mark: a temple doorway, the place where a dwarpal (doorkeeper) stands. */
export function Mark({ className = "size-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="9" className="fill-ink-900 dark:fill-white" />
      <path
        d="M10 25V14a6 6 0 0 1 12 0v11"
        fill="none"
        strokeWidth="2.6"
        strokeLinecap="round"
        className="stroke-brand-500"
      />
      <path
        d="M7 25h18"
        strokeWidth="2.6"
        strokeLinecap="round"
        className="stroke-white dark:stroke-ink-900"
      />
    </svg>
  );
}

export function Shell({ children, label }: { children: ReactNode; label?: string }) {
  const t = useTranslations("Shell");
  return (
    <div className="relative flex min-h-dvh flex-col items-center px-4 py-8 sm:py-14">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-80 bg-[radial-gradient(60%_100%_at_50%_0%,color-mix(in_oklab,var(--color-brand-400)_24%,transparent),transparent_70%)]"
      />
      <header className="relative flex w-full max-w-md items-center gap-2.5">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        {label === undefined ? null : (
          <span className="ml-auto">
            <Badge tone="neutral">{label}</Badge>
          </span>
        )}
      </header>
      <main className="relative mt-6 w-full max-w-md flex-1">{children}</main>
      <footer className="relative mt-10 max-w-md text-center text-xs leading-relaxed text-ink-600 dark:text-ink-400">
        {t("footer1")}
        <br />
        {t("footer2")}
        <span className="mt-3 flex justify-center">
          <LanguageSwitch />
        </span>
      </footer>
    </div>
  );
}
