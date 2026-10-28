/** The analytics counts as one entry for every day of the window, empty days included, so a chart's bars line up with
 *  the calendar rather than with the days that happened to have checks. */

export const OUTCOME_ORDER = ["pass", "fail", "step_up", "retry", "reject"] as const;

export interface DailyCount {
  day: string;
  outcome: string;
  sessions: number;
}

export interface Day {
  day: string;
  counts: Record<string, number>;
  total: number;
}

const DAY_MS = 86_400_000;

/** `days` entries from `since` (a "YYYY-MM-DD" date), adding up each day's rows across policies. */
export function everyDay(since: string, days: number, rows: DailyCount[]): Day[] {
  const start = Date.parse(`${since}T00:00:00Z`);
  if (Number.isNaN(start)) return [];
  const window: Day[] = Array.from({ length: days }, (_, i) => ({
    day: new Date(start + i * DAY_MS).toISOString().slice(0, 10),
    counts: {},
    total: 0,
  }));
  const byDay = new Map(window.map((entry) => [entry.day, entry]));
  for (const row of rows) {
    const entry = byDay.get(row.day);
    if (!entry) continue;
    entry.counts[row.outcome] = (entry.counts[row.outcome] ?? 0) + row.sessions;
    entry.total += row.sessions;
  }
  return window;
}

/** "28 Oct" — the date as it was in UTC, which is how the API counts days. */
export function shortDate(day: string): string {
  return new Date(`${day}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}
