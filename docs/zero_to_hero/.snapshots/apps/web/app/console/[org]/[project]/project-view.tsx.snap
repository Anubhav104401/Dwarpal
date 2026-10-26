"use client";

import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import {
  Alert,
  ConsoleShell,
  Field,
  input,
  panel,
  quietButton,
  smallButton,
} from "@/components/console-shell";
import {
  type Analytics,
  CAN,
  ConsoleClient,
  ConsoleError,
  type PolicyVersion,
  type Role,
  type SessionPage,
  type SessionTrace,
} from "@/lib/console-api";

import { WebhooksPanel } from "./webhooks-panel";

const client = new ConsoleClient();

type Loaded = {
  role: Role;
  projectName: string;
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
            <dt className="text-zinc-500">{name}</dt>
            <dd className="font-mono">{String(value)}</dd>
          </div>
        ))}
      </dl>
      {nested.map(([name, value]) => (
        <details key={name} className="text-xs">
          <summary className="cursor-pointer text-zinc-500">{name}</summary>
          <pre className="mt-1 overflow-x-auto rounded-lg bg-zinc-100 p-2 dark:bg-zinc-950">
            {JSON.stringify(value, null, 2)}
          </pre>
        </details>
      ))}
    </div>
  );
}

export function ProjectView({ org, project }: { org: string; project: string }) {
  const [livemode, setLivemode] = useState(false);
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
      client.sessions(org, project, livemode),
      client.policies(org, project),
    ]);
    const projectName = projects.find((p) => p.id === project)?.name ?? project;
    setState({ role: membership.role, projectName, analytics, page, policies });
  }, [org, project, livemode]);

  useEffect(() => {
    setTrace(null);
    load().catch(() => setError("The console couldn't load this project. Please try again."));
  }, [load]);

  async function more() {
    if (state === null || state === "unavailable" || state.page.nextCursor === null) return;
    const next = await client.sessions(org, project, livemode, state.page.nextCursor);
    setState({
      ...state,
      page: { sessions: [...state.page.sessions, ...next.sessions], nextCursor: next.nextCursor },
    });
  }

  async function addPolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(null);
    try {
      await client.addPolicy(
        org,
        project,
        String(data.get("name")),
        Number(data.get("age")),
        Number(data.get("tries")),
      );
      form.reset();
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  if (state === null) {
    return (
      <ConsoleShell>
        {error === null ? <p className="text-sm text-zinc-500">Loading…</p> : <Alert>{error}</Alert>}
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

  const { role, projectName, analytics, page, policies } = state;
  const outcomes = Object.entries(analytics.totals);
  return (
    <ConsoleShell
      aside={
        <Link className={quietButton} href={`/console/${org}`}>
          Back to the organisation
        </Link>
      }
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{projectName}</h1>
          <p className="mt-1 text-xs text-zinc-500">{project}</p>
        </div>
        <fieldset className="flex rounded-xl border border-zinc-300 p-1 text-sm dark:border-white/15">
          <legend className="sr-only">Mode</legend>
          {[false, true].map((live) => (
            <label
              key={String(live)}
              className={`cursor-pointer rounded-lg px-3 py-1.5 ${livemode === live ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900" : ""}`}
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
          <p className="mt-2 text-sm text-zinc-500">No finished checks yet.</p>
        ) : (
          <ul className="mt-3 flex flex-wrap gap-3">
            {outcomes.map(([outcome, count]) => (
              <li key={outcome} className="rounded-xl border border-zinc-200 px-4 py-2 dark:border-white/10">
                <span className="block text-2xl font-semibold tabular-nums">{count}</span>
                <span className="text-xs capitalize text-zinc-500">{outcome.replace("_", " ")}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[3fr_2fr]">
        <section className={panel} aria-labelledby="sessions">
          <h2 id="sessions" className="text-lg font-semibold">
            Sessions
          </h2>
          {page.sessions.length === 0 ? (
            <p className="mt-2 text-sm text-zinc-500">No sessions yet.</p>
          ) : (
            <table className="mt-3 w-full text-left text-sm">
              <thead className="text-xs uppercase text-zinc-500">
                <tr>
                  <th className="py-2 pr-3 font-medium">Created</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Outcome</th>
                  <th className="py-2 font-medium">
                    <span className="sr-only">Trace</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-white/10">
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
            <p className="mt-2 text-sm text-zinc-500">Choose a session to see why it ended as it did.</p>
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
                  <li
                    key={a.createdAt}
                    className="rounded-xl border border-zinc-200 p-3 dark:border-white/10"
                  >
                    <p className="font-medium">
                      Attempt {index + 1}: {a.outcome}
                      {a.reasons.length > 0 ? ` (${a.reasons.join(", ")})` : ""}
                    </p>
                    <ScoreList scores={a.scores} />
                  </li>
                ))}
              </ol>
              {trace.traced.length === 0 ? <p className="mt-2 text-zinc-500">No attempts.</p> : null}
            </div>
          )}
        </section>
      </div>

      <section className={`${panel} mt-6`} aria-labelledby="policies">
        <h2 id="policies" className="text-lg font-semibold">
          Policies
        </h2>
        <table className="mt-3 w-full text-left text-sm">
          <thead className="text-xs uppercase text-zinc-500">
            <tr>
              <th className="py-2 pr-3 font-medium">Policy</th>
              <th className="py-2 pr-3 font-medium">Age</th>
              <th className="py-2 pr-3 font-medium">Risk budget</th>
              <th className="py-2 font-medium">Attempts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-white/10">
            {policies.map((p) => (
              <tr key={p.id}>
                <td className="py-2 pr-3">
                  <code>{p.id}</code>{" "}
                  {p.preset ? <span className="text-xs text-zinc-500">preset</span> : null}
                </td>
                <td className="py-2 pr-3 tabular-nums">{p.minAge}+</td>
                <td className="py-2 pr-3 tabular-nums">{(p.riskBudget * 100).toFixed(1)} %</td>
                <td className="py-2 tabular-nums">{p.maxFaceAttempts}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {CAN.managePolicies(role) ? (
          <form className="mt-4 grid gap-3 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end" onSubmit={addPolicy}>
            <Field label="New version of policy" id="policy-name">
              <input id="policy-name" className={input} name="name" pattern="[a-z][a-z0-9_]{2,39}" required />
            </Field>
            <Field label="Minimum age" id="policy-age">
              <select id="policy-age" className={input} name="age" defaultValue="18">
                {[13, 16, 18, 21].map((age) => (
                  <option key={age} value={age}>
                    {age}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Face attempts" id="policy-tries">
              <select id="policy-tries" className={input} name="tries" defaultValue="3">
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </Field>
            <button type="submit" className={smallButton}>
              Add version
            </button>
          </form>
        ) : null}
      </section>

      {CAN.manageWebhooks(role) ? (
        <WebhooksPanel client={client} org={org} project={project} livemode={livemode} />
      ) : null}
    </ConsoleShell>
  );
}
