"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Alert, ConsoleShell, panel, quietButton } from "@/components/console-shell";
import { Badge } from "@/components/ui";
import { ConsoleClient, type FaceSource, type ModelInfo } from "@/lib/console-api";

const client = new ConsoleClient();

/** 0.0705 → "7.1 %"; a share nobody measured says so. */
const percent = (share: number | null) => (share === null ? "not measured" : `${(share * 100).toFixed(1)} %`);

/** Where a set of faces came from, in one sentence. */
function Source({ source }: { source: FaceSource }) {
  return (
    <>
      <span className="font-medium">{source.name}</span>
      {source.faces === null ? "" : `, ${source.faces.toLocaleString("en-GB")} faces`} — {source.licence}.
      Ages: {source.ageSource}.
    </>
  );
}

export function ModelView() {
  const [model, setModel] = useState<ModelInfo | "signed-out" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client
      .model()
      .then((found) => setModel(found ?? "signed-out"))
      .catch(() => setError("The console couldn't load the model's details. Please try again."));
  }, []);

  if (model === null || model === "signed-out") {
    return (
      <ConsoleShell>
        {error !== null ? (
          <Alert>{error}</Alert>
        ) : model === null ? (
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
      <h1 className="text-2xl font-semibold tracking-tight">The age model</h1>
      <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-500">
        <span className="font-mono">{model.version}</span>
        {model.calibrated ? (
          <Badge tone="success">Decides live checks</Badge>
        ) : (
          <Badge tone="brand">Test checks only</Badge>
        )}
      </p>
      {model.note && <p className="mt-4 max-w-prose text-sm">{model.note}</p>}

      <section className={`${panel} mt-6`} aria-labelledby="sources">
        <h2 id="sources" className="text-lg font-semibold">
          What it learnt from
        </h2>
        <dl className="mt-3 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[auto_1fr]">
          <dt className="text-ink-500">Permitted use</dt>
          <dd>{model.permittedUse ?? "not stated"}</dd>
          <dt className="text-ink-500">Starting point</dt>
          <dd>
            {model.backbone === null ? (
              "none — a stand-in for testing"
            ) : (
              <span className="font-mono text-xs">{model.backbone}</span>
            )}
          </dd>
          <dt className="text-ink-500">Trained on</dt>
          <dd>
            {model.trainedOn ? <Source source={model.trainedOn} /> : "nothing — a stand-in for testing"}
          </dd>
          <dt className="text-ink-500">Lines set on</dt>
          <dd>{model.calibratedOn ? <Source source={model.calibratedOn} /> : "not measured"}</dd>
        </dl>
      </section>

      <section className={`${panel} mt-6`} aria-labelledby="lines">
        <h2 id="lines" className="text-lg font-semibold">
          Its lines for each age
        </h2>
        <p className="mt-1 max-w-prose text-sm text-ink-500">
          The model gives the chance that a face is at least the age. At or above the pass line the check
          passes; at or below the fail line it fails; in between, the person is offered another way to prove
          their age.{" "}
          {model.calibratedOn === null
            ? "This model's lines were chosen by hand for testing; nothing was measured."
            : "The lines are set on faces of known age, so that no more than the risk budget of those under the age could pass."}
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm tabular-nums">
            <thead className="text-xs uppercase text-ink-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Age</th>
                <th className="py-2 pr-4 font-medium">Risk budget</th>
                <th className="py-2 pr-4 font-medium">Pass at</th>
                <th className="py-2 pr-4 font-medium">Fail at</th>
                <th className="py-2 pr-4 font-medium">Younger people passed, at most</th>
                <th className="py-2 font-medium">Older people failed, at most</th>
              </tr>
            </thead>
            <tbody>
              {model.lines.map((line) => (
                <tr key={line.minAge} className="border-t border-ink-100 dark:border-white/5">
                  <td className="py-2 pr-4 font-semibold">{line.minAge}+</td>
                  <td className="py-2 pr-4">{percent(line.riskBudget)}</td>
                  <td className="whitespace-nowrap py-2 pr-4">≥ {line.tauPass.toFixed(3)}</td>
                  <td className="whitespace-nowrap py-2 pr-4">≤ {line.tauFail.toFixed(3)}</td>
                  <td className="py-2 pr-4">{percent(line.minorBound)}</td>
                  <td className="py-2">{percent(line.adultBound)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </ConsoleShell>
  );
}
