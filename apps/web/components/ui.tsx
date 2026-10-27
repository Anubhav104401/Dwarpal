import type { ReactNode } from "react";

/* Dwarpal's components (Phase 5): the few pieces every page is built from, styled only with the tokens in
   globals.css. Most are class names rather than components, so a `<button>`, `<a>` or `<Link>` can wear them. */

const focusRing = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500";
const motion = "motion-safe:transition motion-safe:duration-(--duration-quick) motion-safe:ease-settle";

const TONES = {
  primary: "bg-ink-900 text-white hover:bg-ink-700 dark:bg-white dark:text-ink-900 dark:hover:bg-ink-200",
  accent: "bg-brand-500 text-ink-950 shadow-lg shadow-brand-500/25 hover:bg-brand-400",
  quiet: "text-ink-600 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-white/10",
} as const;

const SIZES = {
  large: "w-full gap-2 rounded-2xl px-5 py-3.5 text-[15px] font-semibold",
  small: "rounded-xl px-4 py-2.5 text-sm font-semibold",
  compact: "rounded-xl px-3 py-2 text-sm font-medium",
} as const;

/** A button's classes: its tone (how loud) and its size. */
export function button(tone: keyof typeof TONES, size: keyof typeof SIZES): string {
  const shape = "inline-flex items-center justify-center disabled:cursor-not-allowed disabled:opacity-60";
  return `${shape} ${SIZES[size]} ${TONES[tone]} ${motion} ${focusRing}`;
}

/** A raised surface for a group of things; `card` is the verify page's larger one, which rises into view. */
export const panel =
  "rounded-2xl border border-ink-200/80 bg-white/90 p-5 shadow-sm sm:p-6 dark:border-white/10 dark:bg-ink-900/70";
export const card =
  "motion-safe:animate-rise rounded-3xl border border-ink-200/80 bg-white/85 p-6 shadow-xl shadow-ink-900/5 backdrop-blur sm:p-8 dark:border-white/10 dark:bg-ink-900/70 dark:shadow-black/30";

export const input = `w-full rounded-xl border border-ink-300 bg-white px-3.5 py-2.5 text-[15px] outline-none ${motion} focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 dark:border-white/15 dark:bg-ink-950`;

/** A form field: a visible label tied to its control by the control's `id`, as screen readers need. */
export function Field({ label, id, children }: { label: string; id: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-ink-700 dark:text-ink-300">
        {label}
      </label>
      {children}
    </div>
  );
}

/** A message that screen readers announce as soon as it appears: something went wrong. */
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

/** Good news, announced politely (after whatever a screen reader is saying). */
export function Notice({ children }: { children: ReactNode }) {
  return (
    <p
      role="status"
      className="rounded-xl bg-success-500/15 px-3.5 py-2.5 text-sm text-success-700 dark:text-success-300"
    >
      {children}
    </p>
  );
}

const BADGES = {
  brand: "bg-brand-500/15 text-brand-700 dark:text-brand-300",
  success: "bg-success-500/15 text-success-700 dark:text-success-300",
  danger: "bg-red-500/15 text-red-700 dark:text-red-300",
  neutral: "border border-ink-200 font-medium text-ink-600 dark:border-white/10 dark:text-ink-400",
} as const;

/** A short label in a pill. Each tone's text keeps WCAG AA contrast on its own tint, in both themes. */
export function Badge({ tone, children }: { tone: keyof typeof BADGES; children: ReactNode }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGES[tone]}`}>{children}</span>
  );
}
