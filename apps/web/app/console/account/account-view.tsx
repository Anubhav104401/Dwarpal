"use client";

import Link from "next/link";
import QRCode from "qrcode";
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
import { ConsoleClient, ConsoleError, type Me, type PasskeyInfo, type TotpOffer } from "@/lib/console-api";
import { cancelled, creationOptions, passkeysSupported, registrationAnswer } from "@/lib/passkeys";

const client = new ConsoleClient();

/** The secret in groups of four, as authenticator apps show and people type it. */
const grouped = (secret: string) => secret.match(/.{1,4}/g)?.join(" ") ?? secret;

/** A secret on offer, with its otpauth:// address drawn as a QR code (a PNG, as a data: URL), made in the browser. */
type Offer = TotpOffer & { picture: string };

export function AccountView() {
  const [me, setMe] = useState<Me | "signed-out" | null>(null);
  const [offer, setOffer] = useState<Offer | null>(null);
  const [codes, setCodes] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [keys, setKeys] = useState<PasskeyInfo[]>([]);
  const [supported, setSupported] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);

  const load = useCallback(async () => {
    const who = await client.me();
    setMe(who ?? "signed-out");
    if (who !== null) setKeys(await client.passkeys());
  }, []);

  useEffect(() => setSupported(passkeysSupported()), []);

  useEffect(() => {
    load().catch(() => setError("The console couldn't load your account. Please try again."));
  }, [load]);

  async function attempt(work: () => Promise<void>) {
    setError(null);
    try {
      await work();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  const start = () =>
    attempt(async () => {
      const made = await client.totpEnrol();
      setOffer({ ...made, picture: await QRCode.toDataURL(made.uri, { margin: 2, width: 200 }) });
    });

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const code = String(new FormData(event.currentTarget).get("code")).replace(/\s/g, "");
    await attempt(async () => {
      setCodes(await client.totpConfirm(code));
      setOffer(null);
      await load();
    });
  }

  const replaceCodes = () =>
    attempt(async () => {
      setCodes(await client.newRecoveryCodes());
      await load();
    });

  async function turnOff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const code = String(data.get("code")).replace(/\s/g, "");
    await attempt(async () => {
      await client.totpDisable(String(data.get("password")), code);
      setCodes(null);
      await load();
    });
  }

  async function addPasskey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const code = String(data.get("code") ?? "").replace(/\s/g, "");
    setError(null);
    try {
      const options = creationOptions(await client.passkeyOptions());
      const credential = await navigator.credentials.create({ publicKey: options });
      if (!(credential instanceof PublicKeyCredential)) return;
      const name = String(data.get("name"));
      await client.addPasskey(name, registrationAnswer(credential), String(data.get("password")), code);
      form.reset();
      await load();
    } catch (failure) {
      if (cancelled(failure)) return;
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  const removePasskey = (id: string) =>
    attempt(async () => {
      await client.removePasskey(id);
      await load();
    });

  /** A new password (decision D31): the API ends every other session and gives this browser a new one. */
  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const code = String(data.get("code") ?? "").replace(/\s/g, "");
    setPasswordChanged(false);
    await attempt(async () => {
      await client.changePassword(String(data.get("password")), String(data.get("new-password")), code);
      form.reset();
      setPasswordChanged(true);
    });
  }

  /** Erase this account (decision D32), then leave for the console's front page, signed out. */
  async function deleteAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const code = String(data.get("code") ?? "").replace(/\s/g, "");
    await attempt(async () => {
      await client.deleteAccount(String(data.get("password")), code);
      window.location.assign("/console");
    });
  }

  if (me === null || me === "signed-out") {
    return (
      <ConsoleShell>
        {error !== null ? (
          <Alert>{error}</Alert>
        ) : me === null ? (
          <p className="text-sm text-ink-500">Loading…</p>
        ) : (
          <p>
            Please sign in first.{" "}
            <Link className="font-semibold underline" href="/console">
              Go to the console
            </Link>
          </p>
        )}
      </ConsoleShell>
    );
  }

  return (
    <ConsoleShell
      signedIn
      aside={
        <Link className={quietButton} href="/console">
          All organisations
        </Link>
      }
    >
      <h1 className="text-2xl font-semibold tracking-tight">Security</h1>
      <p className="mt-1 text-sm text-ink-500">{me.email}</p>
      {error === null ? null : (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      )}

      <section className={`${panel} mt-6 max-w-xl`} aria-labelledby="totp">
        <h2 id="totp" className="text-lg font-semibold">
          One-time codes
        </h2>
        {codes === null ? null : (
          <div
            className="mt-3 rounded-xl border border-brand-500/40 bg-brand-500/10 p-3 text-sm"
            role="status"
          >
            <p className="font-semibold">
              Your recovery codes — save them somewhere safe. They won't be shown again.
            </p>
            <p className="mt-1">If you lose your phone, each one signs you in once instead of a code.</p>
            <ol className="mt-2 grid grid-cols-2 gap-1 font-mono" data-testid="recovery-codes">
              {codes.map((code) => (
                <li key={code}>{code}</li>
              ))}
            </ol>
          </div>
        )}
        {me.totpEnabled ? (
          <div className="mt-2 space-y-4 text-sm">
            <p role="status">
              <strong>On.</strong> Each time you sign in, you'll be asked for the 6-digit code from your
              authenticator app. Recovery codes left: <strong>{me.recoveryCodesLeft}</strong>.
            </p>
            <button type="button" className={quietButton} onClick={replaceCodes}>
              New recovery codes
            </button>
            <form className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end" onSubmit={turnOff}>
              <Field label="Your password" id="off-password">
                <input
                  id="off-password"
                  className={input}
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                />
              </Field>
              <Field label="Code from your app" id="off-code">
                <input
                  id="off-code"
                  className={input}
                  name="code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\s*(\d\s*){6}"
                  required
                />
              </Field>
              <button type="submit" className={quietButton}>
                Turn off
              </button>
            </form>
          </div>
        ) : offer === null ? (
          <>
            <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
              Off. With one-time codes, a stolen password isn't enough to sign in: you'll also need the code
              your authenticator app shows, which changes every 30 seconds.
            </p>
            <button type="button" className={`${smallButton} mt-4`} onClick={start}>
              Set up one-time codes
            </button>
          </>
        ) : (
          <div className="mt-2 space-y-4 text-sm">
            <div>
              <p className="font-medium">1. Scan this QR code with your authenticator app</p>
              {/* biome-ignore lint/performance/noImgElement: a data: URL made in this browser; next/image would add nothing */}
              <img
                src={offer.picture}
                alt="QR code holding the key, for an authenticator app to scan"
                width={200}
                height={200}
                className="mt-2 rounded-lg bg-white"
              />
              <p className="mt-3 text-ink-600 dark:text-ink-400">Or type this key into the app:</p>
              <code
                className="mt-2 block break-all rounded-lg bg-ink-100 p-2 dark:bg-ink-950"
                data-testid="totp-secret"
              >
                {grouped(offer.secret)}
              </code>
              <a className="mt-2 inline-block font-semibold underline" href={offer.uri}>
                Or open it in an authenticator app on this device
              </a>
            </div>
            <form className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end" onSubmit={confirm}>
              <Field label="2. Enter the code it shows" id="totp-code">
                <input
                  id="totp-code"
                  className={input}
                  name="code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\s*(\d\s*){6}"
                  required
                />
              </Field>
              <button type="submit" className={smallButton}>
                Turn on
              </button>
            </form>
          </div>
        )}
      </section>

      <section className={`${panel} mt-6 max-w-xl`} aria-labelledby="passkeys">
        <h2 id="passkeys" className="text-lg font-semibold">
          Passkeys
        </h2>
        <p className="mt-2 text-sm text-ink-600 dark:text-ink-400">
          A passkey signs you in with your device's fingerprint, face or PIN instead of a password. It works
          only on this site, so a fake site can't trick you into giving it away.
        </p>
        {keys.length === 0 ? null : (
          <ul className="mt-4 divide-y divide-ink-200 text-sm dark:divide-ink-800" data-testid="passkey-list">
            {keys.map((key) => (
              <li key={key.id} className="flex items-center justify-between gap-3 py-2">
                <span>
                  <span className="font-medium">{key.name}</span>
                  <span className="block text-xs text-ink-500">
                    Added {key.createdAt.slice(0, 10)}
                    {key.lastUsedAt === null
                      ? ", not used yet"
                      : `, last used ${key.lastUsedAt.slice(0, 10)}`}
                  </span>
                </span>
                <button
                  type="button"
                  className={quietButton}
                  onClick={() => removePasskey(key.id)}
                  aria-label={`Remove passkey ${key.name}`}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
        {supported ? (
          <form className="mt-4 grid gap-3" onSubmit={addPasskey}>
            <Field label="A name for it" id="passkey-name">
              <input
                id="passkey-name"
                className={input}
                name="name"
                maxLength={60}
                placeholder="Work laptop"
                required
              />
            </Field>
            <Field label="Password, to confirm it's you" id="passkey-password">
              <input
                id="passkey-password"
                className={input}
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
            </Field>
            {me.totpEnabled ? (
              <Field label="One-time code, to confirm it's you" id="passkey-code">
                <input
                  id="passkey-code"
                  className={input}
                  name="code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\s*(\d\s*){6}"
                  required
                />
              </Field>
            ) : null}
            <button type="submit" className={`${smallButton} justify-self-start`}>
              Add a passkey
            </button>
          </form>
        ) : (
          <p className="mt-4 text-sm text-ink-500">This browser can't make passkeys.</p>
        )}
      </section>

      <section className={`${panel} mt-6 max-w-xl`} aria-labelledby="password">
        <h2 id="password" className="text-lg font-semibold">
          Password
        </h2>
        <p className="mt-1 text-sm text-ink-500">
          Changing it signs you out everywhere else; this browser stays signed in.
        </p>
        {passwordChanged ? (
          <p className="mt-3 text-sm font-medium" role="status">
            Password changed. Every other browser has been signed out.
          </p>
        ) : null}
        <form className="mt-4 grid gap-3" onSubmit={changePassword}>
          <Field label="Current password" id="password-current">
            <input
              id="password-current"
              className={input}
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </Field>
          <Field label="New password (at least 12 characters)" id="password-new">
            <input
              id="password-new"
              className={input}
              name="new-password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={256}
              required
            />
          </Field>
          {me.totpEnabled ? (
            <Field label="One-time code, to confirm it's you" id="password-code">
              <input
                id="password-code"
                className={input}
                name="code"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="\s*(\d\s*){6}"
                required
              />
            </Field>
          ) : null}
          <button type="submit" className={`${smallButton} justify-self-start`}>
            Change password
          </button>
        </form>
      </section>

      <section className={`${panel} mt-6 max-w-xl`} aria-labelledby="delete-account">
        <h2 id="delete-account" className="text-lg font-semibold">
          Delete your account
        </h2>
        <p className="mt-1 text-sm text-ink-500">
          Your e-mail address, password, one-time codes and passkeys are erased, and you are signed out
          everywhere. An organisation where you are the only member is closed with you: its keys stop at once.
          If you are the only owner of an organisation with other members, make one of them an owner first.
        </p>
        <form className="mt-4 grid gap-3" onSubmit={deleteAccount}>
          <Field label="Password, to confirm it's you" id="delete-password">
            <input
              id="delete-password"
              className={input}
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </Field>
          {me.totpEnabled ? (
            <Field label="One-time code, to confirm it's you" id="delete-code">
              <input
                id="delete-code"
                className={input}
                name="code"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="\s*(\d\s*){6}"
                required
              />
            </Field>
          ) : null}
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" name="understood" required className="mt-1" />I understand this can't be
            undone.
          </label>
          <button
            type="submit"
            className="justify-self-start rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
          >
            Delete my account
          </button>
        </form>
      </section>
    </ConsoleShell>
  );
}
