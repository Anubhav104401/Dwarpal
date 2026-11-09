"use client";

import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { Alert, ConsoleShell, Field, input, panel, quietButton } from "@/components/console-shell";
import {
  type Analytics,
  CAN,
  ConsoleClient,
  type PolicyVersion,
  type Project,
  type Role,
  type SessionPage,
  type SessionSearch,
  type SessionTrace,
} from "@/lib/console-api";

import { everyDay, OUTCOME_ORDER } from "@/lib/daily";
import { bandText, documentFigures, MEDIAN_TARGET_S, share, withinTarget } from "@/lib/figures";

import { DailyChart } from "./daily-chart";
import { KeysPanel } from "./keys-panel";
import { PolicyEditor } from "./policy-editor";
import { SettingsPanel } from "./settings-panel";
import { WebhooksPanel } from "./webhooks-panel";

const client = new ConsoleClient();

type Loaded = {
  role: Role;
  projectName: string;
  /** The project's own record: its name and allowed origins (null if the list didn't include it). */
  info: Project | null;
  analytics: Analytics;
  page: SessionPage;
  policies: PolicyVersion[];
};

/** The decision's numbers as short lines: plain values first, then anything nested (such as the liveness evidence). */
function ScoreList({ scores }: { scores: Record<string, unknown> }) {
  const entries = Object.entries(scores);
  const plain = entries.filter(([, value]) => typeof value !== "object" || value === null);
  const nested = entries.filter(([, value]) => typeof value === "object" && value !== null);
  return (
    <div className="mt-2 space-y-2">
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
        {plain.map(([name, value]) => (
          <div key={name} className="contents">
            <dt className="text-ink-500">{name}</dt>
            <dd className="font-mono">{String(value)}</dd>
          </div>
        ))}
      </dl>
      {nested.map(([name, value]) => (
        <details key={name} className="text-xs">
          <summary className="cursor-pointer text-ink-500">{name}</summary>
          <pre className="mt-1 overflow-x-auto rounded-lg bg-ink-100 p-2 dark:bg-ink-950">
            {JSON.stringify(value, null, 2)}
          </pre>
        </details>
      ))}
    </div>
  );
}

/** The face checks' headline figures: the median time to a decision against its target, and how often a check was
 * rejected as a likely attack or sent to a stronger check. */
function FaceFigures({ stage }: { stage: Analytics["faceStage"] }) {
  const median = stage.median;
  const figures = [
    {
      name: "Median time to a decision",
      value: median === null ? "—" : bandText(median),
      note:
        median === null
          ? ""
          : withinTarget(median)
            ? `Within the ${MEDIAN_TARGET_S} s target`
            : `Target: ${MEDIAN_TARGET_S} s or less`,
    },
    { name: "Rejected as a likely attack", value: share(stage, "reject"), note: "Liveness or tampering" },
    { name: "Sent to a stronger check", value: share(stage, "step_up"), note: "The age estimate was unsure" },
  ];
  return <Figures title="Face checks" count={`${stage.decided} decided`} figures={figures} />;
}

/** The ID-document checks' headline figures: of the people who reached one — sent there by the face check, or
 * starting there in a live check while no age model is certified — how many finished it (the design's step-up
 * conversion), how many passed, and how many left. */
function DocumentFigures({ stage }: { stage: Analytics["documentStage"] }) {
  const shares = documentFigures(stage);
  const figures = [
    { name: "Finished the check", value: shares.finished, note: "Step-up conversion" },
    { name: "Passed", value: shares.passed, note: "By the document, or an Age Pass" },
    { name: "Left before the end", value: shares.left, note: "Or still on it" },
  ];
  return <Figures title="ID-document checks" count={`${stage.opened} reached`} figures={figures} />;
}

/** A row of headline figures under a small heading: a name, a big value and a note for each. */
function Figures({
  title,
  count,
  figures,
}: {
  title: string;
  count: string;
  figures: Array<{ name: string; value: string; note: string }>;
}) {
  return (
    <div className="mt-5">
      <h3 className="text-sm font-semibold">
        {title} <span className="font-normal text-ink-500">· {count}</span>
      </h3>
      <dl className="mt-2 grid gap-3 sm:grid-cols-3">
        {figures.map((figure) => (
          <div key={figure.name} className="rounded-xl border border-ink-200 px-4 py-3 dark:border-white/10">
            <dt className="text-xs text-ink-500">{figure.name}</dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums">{figure.value}</dd>
            {figure.note && <dd className="text-xs text-ink-500">{figure.note}</dd>}
          </div>
        ))}
      </dl>
    </div>
  );
}

export function ProjectView({ org, project }: { org: string; project: string }) {
  const [livemode, setLivemode] = useState(false);
  const [search, setSearch] = useState<SessionSearch>({});
  const [state, setState] = useState<Loaded | "unavailable" | null>(null);
  const [trace, setTrace] = useState<SessionTrace | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const me = await client.me();
    const membership = me?.organisations.find((o) => o.id === org);
    if (me === null || membership === undefined) return setState("unavailable");
    const [projects, analytics, page, policies] = await Promise.all([
      client.projects(org),
      client.analytics(org, project, livemode),
      client.sessions(org, project, livemode, undefined, search),
      client.policies(org, project),
    ]);
    const info = projects.find((p) => p.id === project) ?? null;
    setState({ role: membership.role, projectName: info?.name ?? project, info, analytics, page, policies });
  }, [org, project, livemode, search]);

  useEffect(() => {
    setTrace(null);
    load().catch(() => setError("The console couldn't load this project. Please try again."));
  }, [load]);

  async function more() {
    if (state === null || state === "unavailable" || state.page.nextCursor === null) return;
    const next = await client.sessions(org, project, livemode, state.page.nextCursor, search);
    setState({
      ...state,
      page: { sessions: [...state.page.sessions, ...next.sessions], nextCursor: next.nextCursor },
    });
  }

  /** A new search: the list starts again from the newest matching session. */
  function searchSessions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const text = (name: string) => String(data.get(name) ?? "").trim() || undefined;
    setSearch({ outcome: text("outcome"), externalRef: text("reference") });
  }

  if (state === null) {
    return (
      <ConsoleShell>
        {error === null ? <p className="text-sm text-ink-500">Loading…</p> : <Alert>{error}</Alert>}
      </ConsoleShell>
    );
  }
  if (state === "unavailable") {
    return (
      <ConsoleShell>
        <p>
          There is no such project, or you aren't signed in as a member.{" "}
          <Link className="font-semibold underline" href="/console">
            Go to the console
          </Link>
        </p>
      </ConsoleShell>
    );
  }

  const { role, projectName, info, analytics, page, policies } = state;
  // In the chart's order, so each total sits where its colour does in the legend; any outcome it doesn't know goes last.
  const rank = (outcome: string) => {
    const place = (OUTCOME_ORDER as readonly string[]).indexOf(outcome);
    return place === -1 ? OUTCOME_ORDER.length : place;
  };
  const outcomes = Object.entries(analytics.totals).sort(([a], [b]) => rank(a) - rank(b));
  return (
    <ConsoleShell
      signedIn
      aside={
        <Link className={quietButton} href={`/console/${org}`}>
          Back to the organisation
        </Link>
      }
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{projectName}</h1>
          <p className="mt-1 text-xs text-ink-500">{project}</p>
        </div>
        <fieldset className="flex rounded-xl border border-ink-300 p-1 text-sm dark:border-white/15">
          <legend className="sr-only">Mode</legend>
          {[false, true].map((live) => (
            <label
              key={String(live)}
              className={`cursor-pointer rounded-lg px-3 py-1.5 ${livemode === live ? "bg-ink-900 text-white dark:bg-white dark:text-ink-900" : ""}`}
            >
              <input
                type="radio"
                name="mode"
                className="sr-only"
                checked={livemode === live}
                onChange={() => setLivemode(live)}
              />
              {live ? "Live" : "Test"}
            </label>
          ))}
        </fieldset>
      </div>
      {error === null ? null : (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      )}

      <section className={`${panel} mt-6`} aria-labelledby="analytics">
        <h2 id="analytics" className="text-lg font-semibold">
          Last 30 days
        </h2>
        {outcomes.length === 0 ? (
          <p className="mt-2 text-sm text-ink-500">No finished checks yet.</p>
        ) : (
          <ul className="mt-3 flex flex-wrap gap-3">
            {outcomes.map(([outcome, count]) => (
              <li key={outcome} className="rounded-xl border border-ink-200 px-4 py-2 dark:border-white/10">
                <span className="block text-2xl font-semibold tabular-nums">{count}</span>
                <span className="text-xs capitalize text-ink-500">{outcome.replace("_", " ")}</span>
              </li>
            ))}
          </ul>
        )}
        {analytics.faceStage.decided > 0 && <FaceFigures stage={analytics.faceStage} />}
        {analytics.documentStage.opened > 0 && <DocumentFigures stage={analytics.documentStage} />}
        {outcomes.length > 0 && <DailyChart days={everyDay(analytics.since, 30, analytics.daily)} />}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[3fr_2fr]">
        <section className={panel} aria-labelledby="sessions">
          <h2 id="sessions" className="text-lg font-semibold">
            Sessions
          </h2>
          <form
            className="mt-3 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
            onSubmit={searchSessions}
          >
            <Field label="Outcome" id="search-outcome">
              <select id="search-outcome" className={input} name="outcome" defaultValue="">
                <option value="">Any</option>
                {OUTCOME_ORDER.map((outcome) => (
                  <option key={outcome} value={outcome}>
                    {outcome.replace("_", " ")}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Website's reference" id="search-reference">
              <input id="search-reference" className={input} name="reference" maxLength={200} />
            </Field>
            <button type="submit" className={quietButton}>
              Search
            </button>
          </form>
          {page.sessions.length === 0 ? (
            <p className="mt-2 text-sm text-ink-500">
              {search.outcome || search.externalRef ? "No sessions match." : "No sessions yet."}
            </p>
          ) : (
            <table className="mt-3 w-full text-left text-sm">
              <thead className="text-xs uppercase text-ink-500">
                <tr>
                  <th className="py-2 pr-3 font-medium">Created</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Outcome</th>
                  <th className="py-2 font-medium">
                    <span className="sr-only">Trace</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200 dark:divide-white/10">
                {page.sessions.map((s) => (
                  <tr key={s.id}>
                    <td className="py-2 pr-3 tabular-nums">{new Date(s.createdAt).toLocaleString()}</td>
                    <td className="py-2 pr-3">{s.status.replace("_", " ")}</td>
                    <td className="py-2 pr-3">{s.outcome ?? "—"}</td>
                    <td className="py-2 text-right">
                      <button
                        type="button"
                        className={quietButton}
                        onClick={() => client.trace(org, project, s.id).then(setTrace)}
                      >
                        Trace
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {page.nextCursor === null ? null : (
            <button type="button" className={`${quietButton} mt-3`} onClick={more}>
              Show older sessions
            </button>
          )}
        </section>

        <section className={panel} aria-labelledby="trace" aria-live="polite">
          <h2 id="trace" className="text-lg font-semibold">
            Decision trace
          </h2>
          {trace === null ? (
            <p className="mt-2 text-sm text-ink-500">Choose a session to see why it ended as it did.</p>
          ) : (
            <div className="mt-2 text-sm">
              <p>
                <code className="text-xs">{trace.id}</code>
              </p>
              <p className="mt-1">
                {trace.policy} · {trace.status.replace("_", " ")} · {trace.outcome ?? "no outcome yet"}
              </p>
              <ol className="mt-3 space-y-3">
                {trace.traced.map((a, index) => (
                  <li key={a.createdAt} className="rounded-xl border border-ink-200 p-3 dark:border-white/10">
                    <p className="font-medium">
                      Attempt {index + 1}: {a.outcome}
                      {a.reasons.length > 0 ? ` (${a.reasons.join(", ")})` : ""}
                    </p>
                    <ScoreList scores={a.scores} />
                  </li>
                ))}
              </ol>
              {trace.traced.length === 0 ? <p className="mt-2 text-ink-500">No attempts.</p> : null}
            </div>
          )}
        </section>
      </div>

      <section className={`${panel} mt-6`} aria-labelledby="policies">
        <h2 id="policies" className="text-lg font-semibold">
          Policies
        </h2>
        <table className="mt-3 w-full text-left text-sm">
          <thead className="text-xs uppercase text-ink-500">
            <tr>
              <th className="py-2 pr-3 font-medium">Policy</th>
              <th className="py-2 pr-3 font-medium">Age</th>
              <th className="py-2 pr-3 font-medium">Risk budget</th>
              <th className="py-2 pr-3 font-medium">Attempts</th>
              <th className="py-2 font-medium">Age Pass</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-200 dark:divide-white/10">
            {policies.map((p) => (
              <tr key={p.id}>
                <td className="py-2 pr-3">
                  <code>{p.id}</code> {p.preset ? <span className="text-xs text-ink-500">preset</span> : null}
                </td>
                <td className="py-2 pr-3 tabular-nums">{p.minAge}+</td>
                <td className="py-2 pr-3 tabular-nums">{(p.riskBudget * 100).toFixed(1)} %</td>
                <td className="py-2 pr-3 tabular-nums">{p.maxFaceAttempts}</td>
                <td className="py-2">{p.acceptAgePass ? "accepted" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {CAN.managePolicies(role) ? (
          <PolicyEditor client={client} org={org} project={project} onAdded={load} />
        ) : null}
      </section>

      {CAN.manageWebhooks(role) ? (
        <WebhooksPanel client={client} org={org} project={project} livemode={livemode} />
      ) : null}

      {CAN.manageKeys(role) ? <KeysPanel client={client} org={org} project={project} /> : null}

      {info === null ? null : (
        <SettingsPanel
          client={client}
          org={org}
          project={info}
          canChange={CAN.manageProjects(role)}
          onSaved={load}
        />
      )}
    </ConsoleShell>
  );
}
