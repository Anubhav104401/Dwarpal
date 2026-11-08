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
import { Badge } from "@/components/ui";
import {
  type AuditLog,
  CAN,
  ConsoleClient,
  ConsoleError,
  type Invitation,
  type Me,
  type Member,
  type NewKey,
  type Project,
  type Role,
} from "@/lib/console-api";
import { originLines } from "@/lib/origins";

const client = new ConsoleClient();
const ROLES: Role[] = ["analyst", "developer", "admin", "owner"];
const SCOPES = ["sessions:read", "sessions:write", "policies:write", "webhooks:write"];

type Loaded = {
  me: Me;
  role: Role;
  name: string;
  members: Member[];
  /** Addresses invited but not signed up yet (decision D44): for those who manage members. */
  invitations: Invitation[];
  projects: Project[];
  audit: AuditLog | null;
};

export function OrganisationView({ org }: { org: string }) {
  const [state, setState] = useState<Loaded | "signed-out" | "not-found" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<NewKey | null>(null);
  const [invited, setInvited] = useState<string | null>(null);

  const load = useCallback(async () => {
    const me = await client.me();
    if (me === null) return setState("signed-out");
    const membership = me.organisations.find((o) => o.id === org);
    if (membership === undefined) return setState("not-found");
    const [members, invitations, projects, audit] = await Promise.all([
      client.members(org),
      CAN.manageMembers(membership.role) ? client.invitations(org) : Promise.resolve([]),
      client.projects(org),
      CAN.readAudit(membership.role) ? client.audit(org) : Promise.resolve(null),
    ]);
    setState({ me, role: membership.role, name: membership.name, members, invitations, projects, audit });
  }, [org]);

  useEffect(() => {
    load().catch(() => setError("The console couldn't load this organisation. Please try again."));
  }, [load]);

  async function addMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(null);
    setInvited(null);
    try {
      const email = String(data.get("email"));
      const added = await client.addMember(org, email, String(data.get("role")) as Role);
      // No account yet: an invitation waits, and they join on signing up with this address (no e-mail is sent).
      if (added.pending) setInvited(email);
      form.reset();
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  async function cancelInvitation(invitation: string) {
    setError(null);
    try {
      await client.cancelInvitation(org, invitation);
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  /** Change a member's role, or remove them (`null`); reload, since it may have been one's own membership. */
  async function changeMember(user: string, role: Role | null) {
    setError(null);
    try {
      await (role === null ? client.removeMember(org, user) : client.changeRole(org, user, role));
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  /** A new project (decisions D28, D29): its name, and the origins its websites run on, one per line. */
  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(null);
    try {
      const origins = originLines(String(data.get("origins") ?? ""));
      await client.createProject(org, String(data.get("name") ?? "").trim(), origins);
      form.reset();
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  async function createKey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setError(null);
    try {
      const scopes = data.getAll("scope").map(String);
      setNewKey(await client.createKey(org, String(data.get("project")), scopes, data.get("live") === "on"));
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  if (state === null) {
    return (
      <ConsoleShell>
        {error === null ? <p className="text-sm text-ink-500">Loading…</p> : <Alert>{error}</Alert>}
      </ConsoleShell>
    );
  }
  if (state === "signed-out" || state === "not-found") {
    return (
      <ConsoleShell>
        <p>
          {state === "signed-out"
            ? "Please sign in first."
            : "There is no such organisation, or you aren't a member."}{" "}
          <Link className="font-semibold underline" href="/console">
            Go to the console
          </Link>
        </p>
      </ConsoleShell>
    );
  }

  const { me, role, name, members, invitations, projects, audit } = state;
  return (
    <ConsoleShell
      signedIn
      aside={
        <>
          <Link className={quietButton} href="/console">
            All organisations
          </Link>
          <span className="hidden text-ink-500 sm:inline">{me.email}</span>
        </>
      }
    >
      <h1 className="text-2xl font-semibold tracking-tight">{name}</h1>
      <p className="mt-1 text-sm text-ink-500">
        Your role: <span className="capitalize">{role}</span>
      </p>
      {error === null ? null : (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className={panel} aria-labelledby="members">
          <h2 id="members" className="text-lg font-semibold">
            Members
          </h2>
          <ul className="mt-3 divide-y divide-ink-200 dark:divide-white/10">
            {members.map((m) => (
              <li key={m.user} className="flex flex-wrap items-center justify-between gap-2 py-2.5 text-sm">
                <span className="break-all">{m.email}</span>
                {CAN.manageMembers(role) && (m.role !== "owner" || role === "owner") ? (
                  <span className="flex items-center gap-1">
                    <select
                      aria-label={`Role of ${m.email}`}
                      className="rounded-lg border border-ink-300 bg-white px-2 py-1 text-sm dark:border-white/15 dark:bg-ink-950"
                      value={m.role}
                      onChange={(event) => changeMember(m.user, event.target.value as Role)}
                    >
                      {ROLES.filter((r) => r !== "owner" || role === "owner").map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className={quietButton}
                      aria-label={`Remove ${m.email}`}
                      onClick={() => changeMember(m.user, null)}
                    >
                      Remove
                    </button>
                  </span>
                ) : (
                  <span className="capitalize text-ink-500">{m.role}</span>
                )}
              </li>
            ))}
          </ul>
          {invitations.length === 0 ? null : (
            <div className="mt-4">
              <h3 className="text-sm font-semibold">Invited, not signed up yet</h3>
              <ul className="mt-1 divide-y divide-ink-200 dark:divide-white/10">
                {invitations.map((i) => (
                  <li key={i.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                    <span className="break-all">
                      {i.email} <span className="capitalize text-ink-500">· {i.role}</span>
                    </span>
                    <button
                      type="button"
                      className={quietButton}
                      aria-label={`Cancel the invitation of ${i.email}`}
                      onClick={() => cancelInvitation(i.id)}
                    >
                      Cancel
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {invited === null ? null : (
            <p className="mt-4 text-sm" role="status">
              {invited} has no account yet, so they are invited: they join when they sign up with this
              address. No e-mail is sent — let them know.
            </p>
          )}
          {CAN.manageMembers(role) ? (
            <form className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end" onSubmit={addMember}>
              <Field label="Add by e-mail" id="member-email">
                <input id="member-email" className={input} name="email" type="email" required />
              </Field>
              <Field label="Role" id="member-role">
                <select id="member-role" className={input} name="role" defaultValue="developer">
                  {ROLES.filter((r) => r !== "owner" || role === "owner").map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </Field>
              <button type="submit" className={smallButton}>
                Add
              </button>
            </form>
          ) : null}
        </section>

        <section className={panel} aria-labelledby="keys">
          <h2 id="keys" className="text-lg font-semibold">
            Projects and API keys
          </h2>
          <ul className="mt-3 space-y-1 text-sm">
            {projects.map((p) => (
              <li key={p.id}>
                <Link
                  className="font-medium underline-offset-2 hover:underline"
                  href={`/console/${org}/${p.id}`}
                >
                  {p.name}
                </Link>{" "}
                <code className="text-xs text-ink-500">{p.id}</code>
                <span className="block text-xs text-ink-500">
                  {p.allowedOrigins.length === 0
                    ? "No allowed origins yet — add your website's on the project's page."
                    : p.allowedOrigins.join(" · ")}
                </span>
              </li>
            ))}
          </ul>
          {CAN.manageProjects(role) ? (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium">New project</summary>
              <form className="mt-3 space-y-3" onSubmit={createProject}>
                <Field label="Name" id="new-project-name">
                  <input id="new-project-name" className={input} name="name" required maxLength={80} />
                </Field>
                <Field label="Allowed origins, one per line" id="new-project-origins">
                  <textarea
                    id="new-project-origins"
                    className={`${input} min-h-20 font-mono`}
                    name="origins"
                    placeholder="https://shop.example"
                  />
                </Field>
                <button type="submit" className={smallButton}>
                  Create project
                </button>
              </form>
            </details>
          ) : null}
          {newKey === null ? null : (
            <div
              className="mt-4 rounded-xl border border-brand-500/40 bg-brand-500/10 p-3 text-sm"
              role="status"
            >
              <p className="font-semibold">Your new key — copy it now. It won't be shown again.</p>
              <code className="mt-2 block break-all" data-testid="new-key">
                {newKey.key}
              </code>
            </div>
          )}
          {CAN.manageKeys(role) && projects.length > 0 ? (
            <form className="mt-4 space-y-3" onSubmit={createKey}>
              <Field label="Project" id="key-project">
                <select id="key-project" className={input} name="project">
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </Field>
              <fieldset>
                <legend className="mb-1.5 text-sm font-medium text-ink-700 dark:text-ink-300">Scopes</legend>
                <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-sm">
                  {SCOPES.map((scope) => (
                    <label key={scope} className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        name="scope"
                        value={scope}
                        defaultChecked={scope.startsWith("sessions")}
                      />
                      <code>{scope}</code>
                    </label>
                  ))}
                </div>
              </fieldset>
              <label className="flex items-center gap-1.5 text-sm">
                <input type="checkbox" name="live" /> Live key (live checks use an ID document until an age
                model is certified)
              </label>
              <button type="submit" className={smallButton}>
                Create key
              </button>
            </form>
          ) : null}
        </section>
      </div>

      {audit === null ? null : (
        <section className={`${panel} mt-6`} aria-labelledby="audit">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 id="audit" className="text-lg font-semibold">
              Audit log
            </h2>
            <Badge tone={audit.intact ? "success" : "danger"}>
              {audit.intact ? "Chain intact" : `Chain broken at entry ${audit.firstBroken}`}
            </Badge>
          </div>
          <table className="mt-3 w-full text-left text-sm">
            <thead className="text-xs uppercase text-ink-500">
              <tr>
                <th className="py-2 pr-3 font-medium">#</th>
                <th className="py-2 pr-3 font-medium">When</th>
                <th className="py-2 pr-3 font-medium">What</th>
                <th className="py-2 font-medium">Who</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-200 dark:divide-white/10">
              {audit.entries.map((e) => (
                <tr key={e.seq}>
                  <td className="py-2 pr-3 tabular-nums text-ink-500">{e.seq}</td>
                  <td className="py-2 pr-3 tabular-nums">{new Date(e.createdAt).toLocaleString()}</td>
                  <td className="py-2 pr-3">
                    <code>{e.action}</code>
                  </td>
                  <td className="py-2 text-ink-500">{e.actor}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </ConsoleShell>
  );
}
