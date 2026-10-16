import type { ReactNode } from "react";

export const card =
  "motion-safe:animate-rise rounded-3xl border border-zinc-200/80 bg-white/85 p-6 shadow-xl shadow-zinc-900/5 backdrop-blur sm:p-8 dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/30";

const button =
  "inline-flex w-full items-center justify-center gap-2 rounded-2xl px-5 py-3.5 text-[15px] font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:cursor-not-allowed disabled:opacity-60";

export const primaryButton = `${button} bg-zinc-900 text-white hover:bg-zinc-700 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200`;

export const accentButton = `${button} bg-brand-500 text-zinc-950 shadow-lg shadow-brand-500/25 hover:bg-brand-400`;

/** Dwarpal's mark: a temple doorway, the place where a dwarpal (doorkeeper) stands. */
export function Mark({ className = "size-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="9" className="fill-zinc-900 dark:fill-white" />
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
        className="stroke-white dark:stroke-zinc-900"
      />
    </svg>
  );
}

export function Shell({ children, label }: { children: ReactNode; label?: string }) {
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
          <span className="ml-auto rounded-full border border-zinc-200 px-3 py-1 text-xs font-medium text-zinc-600 dark:border-white/10 dark:text-zinc-400">
            {label}
          </span>
        )}
      </header>
      <main className="relative mt-6 w-full max-w-md flex-1">{children}</main>
      <footer className="relative mt-10 max-w-md text-center text-xs leading-relaxed text-zinc-500">
        Your photos are checked once and never stored.
        <br />
        Dwarpal never learns who you are — only whether you are old enough.
      </footer>
    </div>
  );
}
