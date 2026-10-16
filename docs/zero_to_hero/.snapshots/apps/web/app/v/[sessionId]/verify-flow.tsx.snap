"use client";

import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { accentButton, card, primaryButton, Shell } from "@/components/shell";
import { type Problem, problemFor, tipFor } from "@/lib/advice";
import { type CapturedFrame, FlowClient, FlowError, type FlowSession } from "@/lib/flow-api";

import { CameraView } from "./camera-view";

type Ending = "pass" | "fail" | "step_up" | "reject";

type Stage =
  | { kind: "loading" }
  | { kind: "intro"; session: FlowSession }
  | { kind: "camera"; session: FlowSession; tip: string | null }
  | { kind: "checking"; session: FlowSession }
  | { kind: "finished"; session: FlowSession; ending: Ending }
  | { kind: "problem"; problem: Problem; requestId: string | null };

/** Read the one-time secret from the link's #fragment, then remove it from the address bar and the history. */
function takeSecretFromLink(): string | null {
  const secret = new URLSearchParams(window.location.hash.slice(1)).get("cs");
  if (secret !== null) {
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }
  return secret;
}

function problemStage(error: unknown): Stage {
  if (error instanceof FlowError) {
    return { kind: "problem", problem: problemFor(error.code), requestId: error.requestId };
  }
  if (error instanceof DOMException && error.name === "NotAllowedError") {
    return { kind: "problem", problem: problemFor("camera_blocked"), requestId: null };
  }
  if (error instanceof DOMException && error.name === "NotFoundError") {
    return { kind: "problem", problem: problemFor("camera_missing"), requestId: null };
  }
  return { kind: "problem", problem: problemFor("unknown"), requestId: null };
}

function endingOf(session: FlowSession): Ending {
  if (session.status === "awaiting_step_up") {
    return "step_up";
  }
  return session.outcome === "pass" || session.outcome === "fail" ? session.outcome : "reject";
}

function Icon({ tone, children }: { tone: string; children: ReactNode }) {
  return (
    <div className={`grid size-12 place-items-center rounded-2xl ${tone}`}>
      <svg
        viewBox="0 0 24 24"
        className="size-6"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        {children}
      </svg>
    </div>
  );
}

const ENDINGS: Record<
  Ending,
  { title: string; body: (s: FlowSession) => string; tone: string; path: string }
> = {
  pass: {
    title: "You're all set",
    body: (s) =>
      `Your age check is complete. ${s.projectName} now knows you are ${s.minAge} or over — nothing else.`,
    tone: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
    path: "M5 12.5l4.5 4.5L19 7.5",
  },
  fail: {
    title: "We couldn't confirm your age",
    body: (s) => `This check couldn't confirm that you are ${s.minAge} or over.`,
    tone: "bg-rose-500/15 text-rose-600 dark:text-rose-400",
    path: "M7 7l10 10M17 7L7 17",
  },
  step_up: {
    title: "We need a stronger check",
    body: (s) =>
      `Photos alone were too close to call. ${s.projectName} will offer another way to confirm your age.`,
    tone: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    path: "M12 7v6m0 4h.01",
  },
  reject: {
    title: "We couldn't complete the check",
    body: () => "This age check couldn't be completed.",
    tone: "bg-rose-500/15 text-rose-600 dark:text-rose-400",
    path: "M7 7l10 10M17 7L7 17",
  },
};

const PROMISES = [
  "We take five quick photos with your camera.",
  "An AI estimates whether you are old enough. It never works out who you are.",
  "The photos are checked once, then deleted. Nothing is stored.",
];

export function VerifyFlow({ sessionId, apiUrl }: { sessionId: string; apiUrl: string }) {
  const [stage, setStage] = useState<Stage>({ kind: "loading" });
  const [leaving, setLeaving] = useState(false);
  const secret = useRef<string | null>(null);
  const flow = useRef<FlowClient | null>(null);

  useEffect(() => {
    let active = true;
    secret.current ??= takeSecretFromLink();
    if (secret.current === null) {
      setStage({ kind: "problem", problem: problemFor("invalid_client_secret"), requestId: null });
      return;
    }
    const client = new FlowClient(apiUrl, sessionId);
    client.start(secret.current).then(
      (session) => {
        if (!active) {
          return;
        }
        flow.current = client;
        setStage(
          session.status === "in_progress"
            ? { kind: "intro", session }
            : { kind: "finished", session, ending: endingOf(session) },
        );
      },
      (error: unknown) => {
        if (active) {
          setStage(problemStage(error));
        }
      },
    );
    return () => {
      active = false;
    };
  }, [apiUrl, sessionId]);

  const onCameraError = useCallback((error: unknown) => setStage(problemStage(error)), []);

  const onCaptured = useCallback(async (session: FlowSession, frames: CapturedFrame[]) => {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setStage({ kind: "checking", session });
    try {
      const result = await client.attempt(frames);
      const updated = { ...session, attemptsRemaining: result.attemptsRemaining };
      setStage(
        result.outcome === "retry"
          ? { kind: "camera", session: updated, tip: tipFor(result.reasons) }
          : { kind: "finished", session: updated, ending: result.outcome },
      );
    } catch (error) {
      setStage(problemStage(error));
    }
  }, []);

  async function leave() {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setLeaving(true);
    try {
      const destination = await client.finish();
      if (destination !== null) {
        window.location.assign(destination);
        return;
      }
    } catch (error) {
      setStage(problemStage(error));
    }
    setLeaving(false);
  }

  if (stage.kind === "loading") {
    return (
      <Shell>
        <div className={`${card} grid h-64 place-items-center`} aria-busy="true">
          <p className="text-sm text-zinc-500">Opening your age check…</p>
        </div>
      </Shell>
    );
  }

  if (stage.kind === "problem") {
    return (
      <Shell>
        <section className={card}>
          <Icon tone="bg-zinc-500/15 text-zinc-600 dark:text-zinc-300">
            <path d="M12 8v5m0 3.5h.01M10.3 3.9L2.6 17.3A2 2 0 0 0 4.3 20.3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
          </Icon>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight">{stage.problem.title}</h1>
          <p className="mt-2 leading-relaxed text-zinc-600 dark:text-zinc-400">{stage.problem.detail}</p>
          {stage.requestId === null ? null : (
            <p className="mt-6 font-mono text-xs text-zinc-500">Reference: {stage.requestId}</p>
          )}
        </section>
      </Shell>
    );
  }

  const { session } = stage;
  const label = `${session.projectName} · ${session.minAge}+`;

  if (stage.kind === "intro") {
    return (
      <Shell label={label}>
        <section className={card}>
          <h1 className="text-2xl font-semibold tracking-tight">Confirm you are {session.minAge} or over</h1>
          <p className="mt-2 leading-relaxed text-zinc-600 dark:text-zinc-400">
            {session.projectName} asks for a quick age check before you continue.
          </p>
          <ol className="mt-6 space-y-3">
            {PROMISES.map((promise, index) => (
              <li key={promise} className="flex gap-3 text-[15px] leading-relaxed">
                <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-500/20 text-xs font-semibold text-brand-600 dark:text-brand-300">
                  {index + 1}
                </span>
                {promise}
              </li>
            ))}
          </ol>
          <button
            type="button"
            className={`${accentButton} mt-8`}
            onClick={() => setStage({ kind: "camera", session, tip: null })}
          >
            Start the camera
          </button>
        </section>
      </Shell>
    );
  }

  if (stage.kind === "camera") {
    return (
      <Shell label={label}>
        <section className={card}>
          <CameraView
            tip={stage.tip}
            onCaptured={(frames) => onCaptured(session, frames)}
            onCameraError={onCameraError}
          />
          <p className="mt-4 text-center text-xs text-zinc-500">
            {session.attemptsRemaining === 1 ? "Last try" : `${session.attemptsRemaining} tries left`}
          </p>
        </section>
      </Shell>
    );
  }

  if (stage.kind === "checking") {
    return (
      <Shell label={label}>
        <section className={`${card} grid h-72 place-items-center text-center`} aria-busy="true">
          <div>
            <div className="mx-auto size-10 motion-safe:animate-spin rounded-full border-[3px] border-brand-500/25 border-t-brand-500" />
            <p className="mt-5 font-medium" role="status">
              Checking your photos…
            </p>
            <p className="mt-1 text-sm text-zinc-500">This takes a second.</p>
          </div>
        </section>
      </Shell>
    );
  }

  const ending = ENDINGS[stage.ending];
  return (
    <Shell label={label}>
      <section className={card}>
        <Icon tone={ending.tone}>
          <path d={ending.path} strokeLinecap="round" strokeLinejoin="round" />
        </Icon>
        <h1 className="mt-5 text-2xl font-semibold tracking-tight">{ending.title}</h1>
        <p className="mt-2 leading-relaxed text-zinc-600 dark:text-zinc-400">{ending.body(session)}</p>
        <button type="button" className={`${primaryButton} mt-8`} disabled={leaving} onClick={leave}>
          {leaving ? "Returning…" : `Continue to ${session.projectName}`}
        </button>
      </section>
    </Shell>
  );
}
