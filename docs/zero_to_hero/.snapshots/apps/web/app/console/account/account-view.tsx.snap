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
import { ConsoleClient, ConsoleError, type Me, type TotpOffer } from "@/lib/console-api";

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

  const load = useCallback(async () => {
    setMe((await client.me()) ?? "signed-out");
  }, []);

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
    </ConsoleShell>
  );
}
