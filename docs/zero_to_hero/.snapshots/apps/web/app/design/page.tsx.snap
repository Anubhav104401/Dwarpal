import type { Metadata } from "next";

import { Mark } from "@/components/shell";
import { Alert, Badge, button, card, Field, input, Notice, panel } from "@/components/ui";

export const metadata: Metadata = { title: "Design system · Dwarpal" };

const SCALES = [
  {
    name: "ink",
    note: "neutrals, a midnight indigo",
    steps: [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950],
  },
  { name: "brand", note: "saffron, the accent", steps: [300, 400, 500, 600, 700] },
  { name: "success", note: "teal", steps: [300, 500, 700] },
];

const TYPE = [
  { label: "Display", className: "text-display font-semibold" },
  { label: "Title", className: "text-2xl font-semibold tracking-tight" },
  { label: "Heading", className: "text-lg font-semibold" },
  { label: "Body", className: "text-[15px] leading-relaxed" },
  { label: "Small", className: "text-sm text-ink-600 dark:text-ink-400" },
  { label: "Code", className: "font-mono text-sm" },
];

/** The design system's specimen: every token and component on one page, which the accessibility tests check in the
 * light and the dark theme — so a change that breaks contrast anywhere fails here first. */
export default function DesignPage() {
  // Written in English only, whatever language the page as a whole is in (decision D2).
  return (
    <div lang="en" className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <header className="flex items-center gap-2.5">
        <Mark />
        <h1 className="text-display font-semibold">Design system</h1>
      </header>
      <p className="mt-3 max-w-2xl text-ink-600 dark:text-ink-400">
        The tokens and components Dwarpal's pages are built from: Geist type, OKLCH colours, and motion that
        stays still for anyone who asks their system for less.
      </p>

      <section className={`${panel} mt-8`} aria-labelledby="colours">
        <h2 id="colours" className="text-lg font-semibold">
          Colours
        </h2>
        {SCALES.map((scale) => (
          <div key={scale.name} className="mt-4">
            <h3 className="text-sm font-semibold">
              {scale.name} <span className="font-normal text-ink-600 dark:text-ink-400">— {scale.note}</span>
            </h3>
            <ul className="mt-2 grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-11">
              {scale.steps.map((step) => (
                <li key={step} className="text-xs">
                  <span
                    className="block h-10 rounded-lg border border-ink-200 dark:border-white/10"
                    style={{ background: `var(--color-${scale.name}-${step})` }}
                  />
                  <span className="mt-1 block font-mono">{step}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section className={`${panel} mt-6`} aria-labelledby="type">
        <h2 id="type" className="text-lg font-semibold">
          Type
        </h2>
        <dl className="mt-3 space-y-3">
          {TYPE.map((t) => (
            <div key={t.label} className="grid gap-1 sm:grid-cols-[8rem_1fr] sm:items-baseline">
              <dt className="text-xs font-medium uppercase text-ink-600 dark:text-ink-400">{t.label}</dt>
              <dd className={t.className}>Look. Decide. Forget.</dd>
            </div>
          ))}
        </dl>
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className={panel} aria-labelledby="buttons">
          <h2 id="buttons" className="text-lg font-semibold">
            Buttons
          </h2>
          <div className="mt-3 space-y-3">
            <button type="button" className={button("accent", "large")}>
              Start the age check
            </button>
            <button type="button" className={button("primary", "large")}>
              Continue
            </button>
            <div className="flex flex-wrap gap-2">
              <button type="button" className={button("primary", "small")}>
                Save
              </button>
              <button type="button" className={button("quiet", "compact")}>
                Cancel
              </button>
              <button type="button" className={button("primary", "small")} disabled>
                Unavailable
              </button>
            </div>
          </div>
        </section>

        <section className={panel} aria-labelledby="forms">
          <h2 id="forms" className="text-lg font-semibold">
            Fields and messages
          </h2>
          <div className="mt-3 space-y-3">
            <Field label="E-mail address" id="specimen-email">
              <input id="specimen-email" className={input} type="email" placeholder="ann@shop.example" />
            </Field>
            <Alert>That e-mail address or password is wrong.</Alert>
            <Notice>Your key was created.</Notice>
            <div className="flex flex-wrap gap-2">
              <Badge tone="brand">Console</Badge>
              <Badge tone="success">Chain intact</Badge>
              <Badge tone="danger">Chain broken</Badge>
              <Badge tone="neutral">Test mode</Badge>
            </div>
          </div>
        </section>
      </div>

      <section className={`${card} mt-6`} aria-labelledby="motion">
        <h2 id="motion" className="text-lg font-semibold">
          Motion
        </h2>
        <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
          This card rose into view in 450 ms, easing to a soft stop. With reduced motion asked for, it simply
          appears.
        </p>
      </section>
    </div>
  );
}
