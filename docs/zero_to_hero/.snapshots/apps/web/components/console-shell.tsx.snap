import type { ReactNode } from "react";

import { Mark } from "./shell";

export const panel =
  "rounded-2xl border border-zinc-200/80 bg-white/90 p-5 shadow-sm sm:p-6 dark:border-white/10 dark:bg-zinc-900/70";

export const input =
  "w-full rounded-xl border border-zinc-300 bg-white px-3.5 py-2.5 text-[15px] outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 dark:border-white/15 dark:bg-zinc-950";

export const smallButton =
  "inline-flex items-center justify-center rounded-xl bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500 disabled:opacity-60 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-200";

export const quietButton =
  "inline-flex items-center justify-center rounded-xl px-3 py-2 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 focus-visible:outline-2 focus-visible:outline-brand-500 dark:text-zinc-400 dark:hover:bg-white/10";

/** A form field: a visible label tied to its control by the control's `id`, as screen readers need. */
export function Field({ label, id, children }: { label: string; id: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {label}
      </label>
      {children}
    </div>
  );
}

/** A message that screen readers announce as soon as it appears. */
export function Alert({ children }: { children: ReactNode }) {
  return (
    <p
      role="alert"
      className="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-300"
    >
      {children}
    </p>
  );
}

/** The console's frame: wider than the verify page, with who is signed in and a way out. */
export function ConsoleShell({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-5xl flex-col px-4 py-6 sm:px-6">
      <header className="flex items-center gap-2.5 border-b border-zinc-200 pb-4 dark:border-white/10">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        <span className="rounded-full bg-brand-500/15 px-2.5 py-0.5 text-xs font-semibold text-brand-600">
          Console
        </span>
        <div className="ml-auto flex items-center gap-2 text-sm">{aside}</div>
      </header>
      <main className="flex-1 py-8">{children}</main>
    </div>
  );
}
