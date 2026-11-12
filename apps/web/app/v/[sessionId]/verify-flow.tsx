"use client";

import { MESSAGE_SOURCE, type VerifyMessage } from "@dwarpal/js";
import { useFormatter, useTranslations } from "next-intl";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { accentButton, card, primaryButton, quietButton, Shell } from "@/components/shell";
import { problemFor, tipFor } from "@/lib/advice";
import {
  forget,
  holderKey,
  type KeptPass,
  keep,
  newKeys,
  presentation,
  type Usable,
  usable,
} from "@/lib/age-pass";
import type { Challenge } from "@/lib/challenge";
import { canFilmDocument } from "@/lib/document-camera";
import { DocumentPhotoError, prepareDocument } from "@/lib/document-photo";
import { type CapturedAttempt, FlowClient, FlowError, type FlowSession } from "@/lib/flow-api";

import { CameraView } from "./camera-view";
import { DocumentCamera } from "./document-camera";

type Ending = "pass" | "fail" | "step_up" | "reject";

type Stage =
  | { kind: "loading" }
  // `passRefused`: an Age Pass was just refused, and removed; the camera is the way on.
  | { kind: "intro"; session: FlowSession; passRefused?: boolean }
  // Tips and problems are keys of their words (`Tips`, `Problems` in `messages/`), put into words when shown.
  | { kind: "camera"; session: FlowSession; tip: string | null }
  | { kind: "checking"; session: FlowSession }
  | { kind: "document"; session: FlowSession; tip: string | null }
  // A computer's webcam, photographing the document inside a guide (D43).
  | { kind: "documentCamera"; session: FlowSession }
  | { kind: "selfie"; session: FlowSession; document: Blob }
  // `earned`: passed just now by a face or document check, so this browser may save Age Passes (never after a
  // pass decided by an Age Pass, nor on a reload).
  | { kind: "finished"; session: FlowSession; ending: Ending; earned?: boolean }
  | { kind: "problem"; problem: string; requestId: string | null };

/** Read the one-time secret from the link's #fragment, then remove it from the address bar and the history. */
function takeSecretFromLink(): string | null {
  const secret = new URLSearchParams(window.location.hash.slice(1)).get("cs");
  if (secret !== null) {
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }
  return secret;
}

/** The website whose frame this page is in, if it is in one and that website is the session's own (decision D16):
 * the only one this page will talk to. The browser enforces the rest — no other website may frame this page. */
function framingWebsite(session: FlowSession): string | null {
  return window.parent !== window ? session.returnOrigin : null;
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

/** How each ending looks: its icon's colours and shape. Its words are in `Verify.ending` (`messages/`). */
const ENDINGS: Record<Ending, { tone: string; path: string }> = {
  pass: { tone: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400", path: "M5 12.5l4.5 4.5L19 7.5" },
  fail: { tone: "bg-rose-500/15 text-rose-600 dark:text-rose-400", path: "M7 7l10 10M17 7L7 17" },
  step_up: { tone: "bg-amber-500/15 text-amber-600 dark:text-amber-400", path: "M12 7v6m0 4h.01" },
  reject: { tone: "bg-rose-500/15 text-rose-600 dark:text-rose-400", path: "M7 7l10 10M17 7L7 17" },
};

const PROMISES = ["promise1", "promise2", "promise3"] as const;

/** What the document check does, said before the person chooses a photo of their document (Phase 6). */
const DOCUMENT_STEPS = ["documentStep1", "documentStep2", "documentStep3"] as const;

/** How many tries the document check allows (the API's MAX_DOCUMENT_ATTEMPTS). */
const DOCUMENT_TRIES = 3;

/** Age Passes saved at once (the API's BATCH): each is used once, so websites can't link one visit to another. */
const PASSES = 20;

/** Saving Age Passes after a passed check: not yet, under way, done (how many, until when), or failed. */
type Saving =
  | { state: "idle" }
  | { state: "saving" }
  | { state: "saved"; count: number; until: Date }
  | { state: "failed" };

/** Refusals that mean this pass will never be accepted: it is removed. Others (an expired nonce, a policy that
 * doesn't take passes) say nothing against the pass itself. */
const PASS_KEPT_ON = new Set(["age_pass_nonce_expired", "age_pass_not_accepted"]);

export function VerifyFlow({ sessionId, apiUrl }: { sessionId: string; apiUrl: string }) {
  const [stage, setStage] = useState<Stage>({ kind: "loading" });
  const [leaving, setLeaving] = useState(false);
  const [framedBy, setFramedBy] = useState<string | null>(null);
  const [documentTries, setDocumentTries] = useState(DOCUMENT_TRIES);
  // Whether the document can be photographed with this computer's webcam: known only in the browser.
  const [computer, setComputer] = useState(false);
  const [pass, setPass] = useState<Usable | null>(null);
  const [saving, setSaving] = useState<Saving>({ state: "idle" });
  const t = useTranslations("Verify");
  const format = useFormatter();
  const tips = useTranslations("Tips");
  const problems = useTranslations("Problems");
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
        setFramedBy(framingWebsite(session));
        // An Age Pass is offered only on this page's own tab: inside another website's frame, the browser keeps a
        // separate store for each website, so passes saved there would be found only on that website again.
        if (session.status === "in_progress" && session.acceptAgePass && framingWebsite(session) === null) {
          usable(session.minAge, session.livemode).then(
            (found) => {
              if (active) setPass(found);
            },
            () => undefined, // no storage in this browser (a private window, say): the camera, as always
          );
        }
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

  const getChallenge = useCallback((): Promise<Challenge> => {
    const client = flow.current;
    return client === null ? Promise.reject(new Error("the check has not started")) : client.challenge();
  }, []);

  const onCaptured = useCallback(async (session: FlowSession, captured: CapturedAttempt) => {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setStage({ kind: "checking", session });
    try {
      const result = await client.attempt(captured);
      const updated = { ...session, attemptsRemaining: result.attemptsRemaining };
      setStage(
        result.outcome === "retry"
          ? { kind: "camera", session: updated, tip: tipFor(result.reasons) }
          : { kind: "finished", session: updated, ending: result.outcome, earned: result.outcome === "pass" },
      );
    } catch (error) {
      setStage(problemStage(error));
    }
  }, []);

  /** Answer the check with an Age Pass: a nonce from the server, the pass's one line signed over it, and done. */
  const answerWithPass = useCallback(async (session: FlowSession, chosen: Usable) => {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setStage({ kind: "checking", session });
    try {
      const { nonce, audience } = await client.agePassNonce();
      const { pass: kept, key } = chosen.kept;
      await client.presentAgePass(await presentation(kept, key, chosen.line, nonce, audience));
      setPass(null);
      await forget(chosen.id); // used once, never again
      setStage({ kind: "finished", session, ending: "pass" });
    } catch (error) {
      if (error instanceof FlowError && error.code.startsWith("age_pass_")) {
        setPass(null);
        if (!PASS_KEPT_ON.has(error.code)) {
          await forget(chosen.id).catch(() => undefined);
        }
        setStage({ kind: "intro", session, passRefused: true });
        return;
      }
      setStage(problemStage(error));
    }
  }, []);

  useEffect(() => setComputer(canFilmDocument()), []);

  /** The document check: the chosen or taken photo, prepared for sending (scaled, re-encoded, under the size
   * limit). */
  const onDocumentChosen = useCallback(async (session: FlowSession, file: Blob | undefined) => {
    if (file === undefined) {
      return;
    }
    try {
      setStage({ kind: "selfie", session, document: await prepareDocument(file) });
    } catch (error) {
      const tip = error instanceof DocumentPhotoError ? "document_unusable" : null;
      setStage({ kind: "document", session, tip });
    }
  }, []);

  /** The webcam couldn't be opened for the document: back to the choice, with a note to choose a file instead. */
  const onDocumentCameraUnavailable = useCallback(() => {
    setStage((current) =>
      current.kind === "documentCamera"
        ? { kind: "document", session: current.session, tip: "camera_unavailable" }
        : current,
    );
  }, []);

  const onSelfieCaptured = useCallback(
    async (session: FlowSession, document: Blob, captured: CapturedAttempt) => {
      const client = flow.current;
      if (client === null) {
        return;
      }
      setStage({ kind: "checking", session });
      try {
        const result = await client.documentAttempt(document, captured);
        setDocumentTries(result.attemptsRemaining);
        setStage(
          result.outcome === "retry"
            ? { kind: "document", session, tip: tipFor(result.reasons) }
            : {
                kind: "finished",
                session,
                ending: result.outcome === "step_up" ? "fail" : result.outcome,
                earned: result.outcome === "pass",
              },
        );
      } catch (error) {
        setStage(problemStage(error));
      }
    },
    [],
  );

  /** Save a batch of Age Passes in this browser: one key pair per pass, the public halves sent, the passes kept
   * with their private halves (which can't be read out again). */
  async function savePasses(session: FlowSession) {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setSaving({ state: "saving" });
    try {
      const pairs = await newKeys(PASSES);
      const issued = await client.issueAgePasses(
        await Promise.all(pairs.map((pair) => holderKey(pair.publicKey))),
      );
      const expiresAt = Date.parse(issued.expiresAt);
      const kept: KeptPass[] = [];
      issued.passes.forEach((signed, index) => {
        const pair = pairs[index];
        if (pair !== undefined) {
          kept.push({
            pass: signed,
            key: pair.privateKey,
            lines: issued.lines,
            expiresAt,
            livemode: session.livemode,
          });
        }
      });
      await keep(kept);
      setSaving({ state: "saved", count: kept.length, until: new Date(expiresAt) });
    } catch {
      setSaving({ state: "failed" });
    }
  }

  /** Tell the framing website something, at its origin only: nothing reaches any other page. */
  function tellWebsite(message: VerifyMessage) {
    if (framedBy !== null) {
      window.parent.postMessage(message, framedBy);
    }
  }

  async function leave() {
    const client = flow.current;
    if (client === null) {
      return;
    }
    setLeaving(true);
    try {
      const destination = await client.finish();
      if (destination !== null && framedBy !== null) {
        // In a frame, the website moves its whole page to the return address (the SDK checks it is its own).
        tellWebsite({ source: MESSAGE_SOURCE, type: "finished", sessionId, redirectUrl: destination });
        return;
      }
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
          <p className="text-sm text-ink-600 dark:text-ink-400">{t("opening")}</p>
        </div>
      </Shell>
    );
  }

  if (stage.kind === "problem") {
    return (
      <Shell>
        <section className={card}>
          <Icon tone="bg-ink-500/15 text-ink-600 dark:text-ink-300">
            <path d="M12 8v5m0 3.5h.01M10.3 3.9L2.6 17.3A2 2 0 0 0 4.3 20.3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
          </Icon>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight">{problems(`${stage.problem}.title`)}</h1>
          <p className="mt-2 leading-relaxed text-ink-600 dark:text-ink-400">
            {problems(`${stage.problem}.detail`)}
          </p>
          {framedBy === null ? null : (
            <button
              type="button"
              className={`${primaryButton} mt-8`}
              onClick={() => tellWebsite({ source: MESSAGE_SOURCE, type: "full_page", sessionId })}
            >
              {t("fullPage")}
            </button>
          )}
          {stage.requestId === null ? null : (
            <p className="mt-6 font-mono text-xs text-ink-600 dark:text-ink-400">
              {t("reference", { id: stage.requestId })}
            </p>
          )}
        </section>
      </Shell>
    );
  }

  const { session } = stage;
  const label = t("label", { project: session.projectName, age: session.minAge });
  const tries = (count: number) => t("tries", { count });

  if (stage.kind === "intro") {
    // A document-only check (D24) says what the document check does, and leads to it instead of the camera.
    const steps = session.documentOnly ? DOCUMENT_STEPS : PROMISES;
    return (
      <Shell label={label}>
        <section className={card}>
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("introTitle", { age: session.minAge })}
          </h1>
          <p className="mt-2 leading-relaxed text-ink-600 dark:text-ink-400">
            {t(session.documentOnly ? "introLeadDocument" : "introLead", { project: session.projectName })}
          </p>
          <ol className="mt-6 space-y-3">
            {steps.map((promise, index) => (
              <li key={promise} className="flex gap-3 text-[15px] leading-relaxed">
                <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-500/20 text-xs font-semibold text-brand-700 dark:text-brand-300">
                  {index + 1}
                </span>
                {t(promise)}
              </li>
            ))}
          </ol>
          {stage.passRefused ? (
            <p
              className="mt-6 rounded-xl bg-amber-500/15 px-4 py-3 text-sm text-amber-800 dark:text-amber-200"
              role="status"
            >
              {t("agePassRefused")}
            </p>
          ) : null}
          {pass === null ? null : (
            <div className="mt-6 rounded-2xl border border-brand-500/40 bg-brand-500/10 p-4">
              <h2 className="font-semibold">{t("agePassTitle")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-ink-700 dark:text-ink-300">
                {t("agePassBody", { project: session.projectName, line: pass.line })}
              </p>
              <button
                type="button"
                className={`${accentButton} mt-4`}
                onClick={() => answerWithPass(session, pass)}
              >
                {t("agePassUse")}
              </button>
            </div>
          )}
          <button
            type="button"
            className={`${pass === null ? accentButton : quietButton} mt-8`}
            onClick={() =>
              setStage(
                session.documentOnly
                  ? { kind: "document", session, tip: null }
                  : { kind: "camera", session, tip: null },
              )
            }
          >
            {t(session.documentOnly ? "useDocument" : "startCamera")}
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
            tip={stage.tip === null ? null : tips(stage.tip)}
            getChallenge={getChallenge}
            onCaptured={(captured) => onCaptured(session, captured)}
            onCameraError={onCameraError}
          />
          <p className="mt-4 text-center text-xs text-ink-600 dark:text-ink-400">
            {tries(session.attemptsRemaining)}
          </p>
        </section>
      </Shell>
    );
  }

  if (stage.kind === "document") {
    return (
      <Shell label={label}>
        <section className={card}>
          <h1 className="text-2xl font-semibold tracking-tight">{t("documentTitle")}</h1>
          {stage.tip === null ? null : (
            <p
              className="mt-3 rounded-xl bg-amber-500/15 px-4 py-3 text-sm text-amber-800 dark:text-amber-200"
              role="alert"
            >
              {tips(stage.tip)}
            </p>
          )}
          <ol className="mt-6 space-y-3">
            {DOCUMENT_STEPS.map((step, index) => (
              <li key={step} className="flex gap-3 text-[15px] leading-relaxed">
                <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-500/20 text-xs font-semibold text-brand-700 dark:text-brand-300">
                  {index + 1}
                </span>
                {t(step)}
              </li>
            ))}
          </ol>
          {/* Test sessions also take an Aadhaar Secure QR as the document (Part 7); said with what is read from it. */}
          {session.livemode ? null : (
            <p className="mt-4 rounded-xl bg-ink-500/10 px-4 py-3 text-sm leading-relaxed text-ink-700 dark:text-ink-300">
              {t("documentAadhaar")}
            </p>
          )}
          {/* On a computer, its webcam first (D43); the file chooser stays, as the way for everyone else. */}
          {computer ? (
            <button
              type="button"
              className={`${accentButton} mt-8`}
              onClick={() => setStage({ kind: "documentCamera", session })}
            >
              {t("documentCameraButton")}
            </button>
          ) : null}
          {/* The real control is the hidden file input inside; the label wears the button's look, and its focus ring
              when the input has keyboard focus. */}
          <label
            className={`${computer ? `${quietButton} mt-3` : `${accentButton} mt-8`} cursor-pointer has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-brand-500`}
          >
            {t(computer ? "documentFileButton" : "documentButton")}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              capture="environment"
              className="sr-only"
              onChange={(event) => onDocumentChosen(session, event.target.files?.[0])}
            />
          </label>
          <p className="mt-4 text-center text-xs text-ink-600 dark:text-ink-400">{tries(documentTries)}</p>
        </section>
      </Shell>
    );
  }

  if (stage.kind === "documentCamera") {
    return (
      <Shell label={label}>
        <section className={card}>
          <h1 className="text-2xl font-semibold tracking-tight">{t("documentTitle")}</h1>
          <div className="mt-6">
            <DocumentCamera
              onTaken={(photo) => onDocumentChosen(session, photo)}
              onChooseFile={() => setStage({ kind: "document", session, tip: null })}
              onUnavailable={onDocumentCameraUnavailable}
            />
          </div>
          <p className="mt-4 text-center text-xs text-ink-600 dark:text-ink-400">{tries(documentTries)}</p>
        </section>
      </Shell>
    );
  }

  if (stage.kind === "selfie") {
    const { document } = stage;
    return (
      <Shell label={label}>
        <section className={card}>
          <p className="mb-4 text-sm text-ink-600 dark:text-ink-400">{t("selfieLead")}</p>
          <CameraView
            tip={null}
            getChallenge={getChallenge}
            onCaptured={(captured) => onSelfieCaptured(session, document, captured)}
            onCameraError={onCameraError}
          />
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
              {t("checking")}
            </p>
            <p className="mt-1 text-sm text-ink-600 dark:text-ink-400">{t("checkingDetail")}</p>
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
        <h1 className="mt-5 text-2xl font-semibold tracking-tight">{t(`ending.${stage.ending}.title`)}</h1>
        <p className="mt-2 leading-relaxed text-ink-600 dark:text-ink-400">
          {t(`ending.${stage.ending}.body`, { project: session.projectName, age: session.minAge })}
        </p>
        {stage.ending === "step_up" ? (
          <>
            <button
              type="button"
              className={`${accentButton} mt-8`}
              onClick={() => setStage({ kind: "document", session, tip: null })}
            >
              {t("useDocument")}
            </button>
            <button type="button" className={`${quietButton} mt-3`} disabled={leaving} onClick={leave}>
              {leaving ? t("returning") : t("notNow", { project: session.projectName })}
            </button>
          </>
        ) : (
          <>
            {stage.ending === "pass" && stage.earned && session.acceptAgePass && framedBy === null ? (
              <div className="mt-6 rounded-2xl border border-ink-200 p-4 dark:border-white/10">
                {saving.state === "saved" ? (
                  <p className="text-sm font-medium" role="status">
                    {t("agePassSaved", {
                      count: saving.count,
                      date: format.dateTime(saving.until, { dateStyle: "long" }),
                    })}
                  </p>
                ) : (
                  <>
                    <h2 className="font-semibold">{t("agePassSaveTitle")}</h2>
                    <p className="mt-1 text-sm leading-relaxed text-ink-700 dark:text-ink-300">
                      {t("agePassSaveBody", { age: session.minAge })}
                    </p>
                    {saving.state === "failed" ? (
                      <p className="mt-2 text-sm text-rose-700 dark:text-rose-300" role="alert">
                        {t("agePassSaveFailed")}
                      </p>
                    ) : null}
                    <button
                      type="button"
                      className={`${quietButton} mt-4`}
                      disabled={saving.state === "saving"}
                      onClick={() => savePasses(session)}
                    >
                      {saving.state === "saving" ? t("agePassSaving") : t("agePassSave")}
                    </button>
                  </>
                )}
              </div>
            ) : null}
            <button type="button" className={`${primaryButton} mt-8`} disabled={leaving} onClick={leave}>
              {leaving ? t("returning") : t("continue", { project: session.projectName })}
            </button>
          </>
        )}
      </section>
    </Shell>
  );
}
