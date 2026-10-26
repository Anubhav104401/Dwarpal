"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";

import {
  Alert,
  ConsoleShell,
  Field,
  input,
  panel,
  quietButton,
  smallButton,
} from "@/components/console-shell";
import { ConsoleClient, ConsoleError, type Me } from "@/lib/console-api";

const client = new ConsoleClient();

type Mode = "sign-in" | "sign-up";

/** Plain words for the refusals a person can do something about; anything else is shown as the API said it. */
function explain(error: unknown): string {
  if (!(error instanceof ConsoleError)) return "Something went wrong. Please try again.";
  const words: Record<string, string> = {
    invalid_credentials: "That e-mail address or password is wrong.",
    totp_required: "Enter the 6-digit code from your authenticator app.",
    invalid_totp: "That code is wrong or has already been used.",
    too_many_sign_ins: "Too many attempts. Wait a minute, then try again.",
    email_taken: "An account with this e-mail address already exists. Sign in instead.",
    weak_password: "Use a password of at least 12 characters.",
    invalid_email: "That doesn't look like an e-mail address.",
  };
  return words[error.code] ?? error.message;
}

export function ConsoleHome() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);
  const [mode, setMode] = useState<Mode>("sign-in");
  const [needsCode, setNeedsCode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    client.me().then(setMe, () => setMe(null));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const text = (name: string) => String(form.get(name) ?? "");
    setBusy(true);
    setError(null);
    try {
      setMe(
        mode === "sign-in"
          ? await client.signIn(text("email"), text("password"), text("code") || undefined)
          : await client.signUp(text("email"), text("password"), text("organisation")),
      );
    } catch (failure) {
      if (failure instanceof ConsoleError && failure.code === "totp_required") setNeedsCode(true);
      setError(explain(failure));
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await client.signOut();
    setMe(null);
  }

  if (me === undefined) {
    return (
      <ConsoleShell>
        <p className="text-sm text-zinc-500" aria-live="polite">
          Loading…
        </p>
      </ConsoleShell>
    );
  }

  if (me !== null) {
    return (
      <ConsoleShell
        aside={
          <>
            <span className="hidden text-zinc-500 sm:inline">{me.email}</span>
            <Link className={quietButton} href="/console/account">
              Security
            </Link>
            <button type="button" className={quietButton} onClick={signOut}>
              Sign out
            </button>
          </>
        }
      >
        <h1 className="text-2xl font-semibold tracking-tight">Your organisations</h1>
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {me.organisations.map((org) => (
            <li key={org.id}>
              <Link
                href={`/console/${org.id}`}
                className={`${panel} block transition hover:border-brand-500`}
              >
                <span className="block font-semibold">{org.name}</span>
                <span className="mt-1 block text-sm capitalize text-zinc-500">{org.role}</span>
              </Link>
            </li>
          ))}
        </ul>
      </ConsoleShell>
    );
  }

  const signingUp = mode === "sign-up";
  return (
    <ConsoleShell>
      <section className={`${panel} mx-auto max-w-md`}>
        <h1 className="text-2xl font-semibold tracking-tight">
          {signingUp ? "Create an account" : "Sign in"}
        </h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          For the people who run websites with Dwarpal. The people whose age is checked never need an account.
        </p>
        <form className="mt-6 space-y-4" onSubmit={submit}>
          <Field label="E-mail address" id="email">
            <input id="email" className={input} name="email" type="email" autoComplete="email" required />
          </Field>
          <Field label="Password" id="password">
            <input
              id="password"
              className={input}
              name="password"
              type="password"
              autoComplete={signingUp ? "new-password" : "current-password"}
              minLength={signingUp ? 12 : undefined}
              required
            />
          </Field>
          {signingUp ? (
            <Field label="Organisation name" id="organisation">
              <input
                id="organisation"
                className={input}
                name="organisation"
                autoComplete="organization"
                required
              />
            </Field>
          ) : null}
          {needsCode && !signingUp ? (
            <Field label="6-digit code from your authenticator app" id="code">
              <input
                id="code"
                className={input}
                name="code"
                inputMode="numeric"
                pattern="[0-9]{6}"
                autoComplete="one-time-code"
                required
              />
            </Field>
          ) : null}
          {error === null ? null : <Alert>{error}</Alert>}
          <button type="submit" className={`${smallButton} w-full`} disabled={busy}>
            {signingUp ? "Create account" : "Sign in"}
          </button>
        </form>
        <button
          type="button"
          className={`${quietButton} mt-4 w-full`}
          onClick={() => {
            setMode(signingUp ? "sign-in" : "sign-up");
            setError(null);
          }}
        >
          {signingUp ? "I already have an account" : "Create an account"}
        </button>
      </section>
    </ConsoleShell>
  );
}
