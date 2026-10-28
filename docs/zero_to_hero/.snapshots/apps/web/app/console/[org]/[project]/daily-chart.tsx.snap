"use client";

import { useState } from "react";

import { type Day, OUTCOME_ORDER, shortDate } from "@/lib/daily";

// One fixed colour per outcome, in a fixed order, checked for colour-blind separation on both surfaces. Three of the
// light ones are under 3:1 against white, so the table beneath gives the same numbers as text.
const COLOUR: Record<string, string> = {
  pass: "bg-[#2a78d6] dark:bg-[#3987e5]",
  fail: "bg-[#eb6834] dark:bg-[#d95926]",
  step_up: "bg-[#1baf7a] dark:bg-[#199e70]",
  retry: "bg-[#eda100] dark:bg-[#c98500]",
  reject: "bg-[#e87ba4] dark:bg-[#d55181]",
};

const label = (outcome: string) => outcome.replace("_", " ");

/** Finished checks per day, stacked by outcome, with each day's numbers on hover and the whole series as a table. */
export function DailyChart({ days }: { days: Day[] }) {
  const [active, setActive] = useState<number | null>(null);
  const peak = Math.max(1, ...days.map((d) => d.total));
  const total = days.reduce((sum, d) => sum + d.total, 0);
  const shown = active === null ? null : days[active];
  // The day's numbers sit beside its bar, on whichever side has more room, so they never cover the bar itself.
  const middle = active === null ? 0 : ((active + 0.5) / days.length) * 100;
  const beside =
    middle < 50 ? { left: `calc(${middle}% + 12px)` } : { right: `calc(${100 - middle}% + 12px)` };
  const first = days[0];
  const last = days.at(-1);
  if (!first || !last) return null;

  return (
    <figure className="mt-4" data-testid="daily-chart">
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-600 dark:text-ink-300">
        {OUTCOME_ORDER.map((outcome) => (
          <li key={outcome} className="flex items-center gap-1.5 capitalize">
            <span className={`size-2.5 rounded-sm ${COLOUR[outcome]}`} aria-hidden="true" />
            {label(outcome)}
          </li>
        ))}
      </ul>

      <div className="relative mt-3">
        {/* Each day is a button only so that hovering or tabbing to it shows its numbers; its label says them too. */}
        <fieldset
          aria-label={`${total} finished checks from ${shortDate(first.day)} to ${shortDate(last.day)}; the busiest day had ${peak}.`}
          className="flex h-36 items-end gap-0.5 border-y border-t-ink-100 border-b-ink-300 dark:border-t-white/5 dark:border-b-white/20"
          onMouseLeave={() => setActive(null)}
        >
          {days.map((d, i) => (
            <button
              type="button"
              key={d.day}
              aria-label={`${shortDate(d.day)}: ${d.total} ${d.total === 1 ? "check" : "checks"}`}
              className={`flex h-full flex-1 flex-col justify-end ${active === i ? "bg-ink-100 dark:bg-white/5" : ""}`}
              onMouseEnter={() => setActive(i)}
              onFocus={() => setActive(i)}
              onBlur={() => setActive(null)}
            >
              <div
                className="flex flex-col-reverse gap-0.5 overflow-hidden rounded-t"
                style={{ height: `${(d.total / peak) * 100}%` }}
              >
                {OUTCOME_ORDER.filter((outcome) => d.counts[outcome]).map((outcome) => (
                  <div
                    key={outcome}
                    className={`min-h-px ${COLOUR[outcome]}`}
                    style={{ flexGrow: d.counts[outcome] }}
                  />
                ))}
              </div>
            </button>
          ))}
        </fieldset>
        <span className="absolute -top-1 left-0 text-xs tabular-nums text-ink-500">{peak}</span>
        {shown && (
          <div
            style={beside}
            className="pointer-events-none absolute top-4 rounded-lg border border-ink-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-white/10 dark:bg-ink-900"
          >
            <p className="font-semibold">
              {shortDate(shown.day)}: {shown.total} {shown.total === 1 ? "check" : "checks"}
            </p>
            {OUTCOME_ORDER.filter((outcome) => shown.counts[outcome]).map((outcome) => (
              <p
                key={outcome}
                className="flex items-center gap-1.5 capitalize text-ink-600 dark:text-ink-300"
              >
                <span className={`size-2 rounded-sm ${COLOUR[outcome]}`} aria-hidden="true" />
                {label(outcome)} <span className="tabular-nums">{shown.counts[outcome]}</span>
              </p>
            ))}
          </div>
        )}
      </div>

      <figcaption className="mt-1 flex justify-between text-xs text-ink-500">
        <span>{shortDate(first.day)}</span>
        <span>{shortDate(last.day)}</span>
      </figcaption>

      <details className="mt-3 text-sm">
        <summary className="cursor-pointer text-ink-600 dark:text-ink-300">Show as a table</summary>
        <table className="mt-2 w-full text-left text-xs tabular-nums">
          <thead className="uppercase text-ink-500">
            <tr>
              <th className="py-1 font-medium">Day</th>
              {OUTCOME_ORDER.map((outcome) => (
                <th key={outcome} className="py-1 font-medium">
                  {label(outcome)}
                </th>
              ))}
              <th className="py-1 font-medium">All</th>
            </tr>
          </thead>
          <tbody>
            {days
              .filter((d) => d.total > 0)
              .map((d) => (
                <tr key={d.day} className="border-t border-ink-100 dark:border-white/5">
                  <td className="py-1">{shortDate(d.day)}</td>
                  {OUTCOME_ORDER.map((outcome) => (
                    <td key={outcome} className="py-1">
                      {d.counts[outcome] ?? 0}
                    </td>
                  ))}
                  <td className="py-1 font-semibold">{d.total}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
