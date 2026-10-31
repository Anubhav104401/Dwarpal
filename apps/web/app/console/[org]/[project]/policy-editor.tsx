"use client";

import { type FormEvent, useEffect, useState } from "react";

import { Alert, Field, input, smallButton } from "@/components/console-shell";
import { type ConsoleClient, ConsoleError, type ModelInfo } from "@/lib/console-api";
import { agesText, defaultLine, lineKey, lineLabel, percent } from "@/lib/projection";

type Props = { client: ConsoleClient; org: string; project: string; onAdded: () => Promise<void> };

/**
 * Add a version of one of the project's own policies. It offers exactly the lines the age model in use has — any
 * other would be refused — and shows, for the chosen line, how adults just over the age fared when it was measured:
 * the share a policy would send to a stronger check (the design's "projected adult step-up rate").
 */
export function PolicyEditor({ client, org, project, onAdded }: Props) {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [chosen, setChosen] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    client.model().then(
      (info) => {
        setModel(info);
        const first = info === null ? undefined : defaultLine(info.lines);
        setChosen(first === undefined ? "" : lineKey(first));
      },
      () => setError("The console couldn't load the age model's lines. Please try again."),
    );
  }, [client]);

  const line = model?.lines.find((candidate) => lineKey(candidate) === chosen);

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (line === undefined) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    setError(null);
    try {
      await client.addPolicy(
        org,
        project,
        String(data.get("name")),
        line.minAge,
        Number(data.get("tries")),
        line.riskBudget,
      );
      form.reset();
      await onAdded();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  if (model === null || line === undefined) {
    return error === null ? null : <Alert>{error}</Alert>;
  }

  return (
    <>
      {error === null ? null : <Alert>{error}</Alert>}
      <form className="mt-4 grid gap-3 sm:grid-cols-[2fr_2fr_1fr_auto] sm:items-end" onSubmit={add}>
        <Field label="New version of policy" id="policy-name">
          <input id="policy-name" className={input} name="name" pattern="[a-z][a-z0-9_]{2,39}" required />
        </Field>
        <Field label="Age line" id="policy-line">
          <select
            id="policy-line"
            className={input}
            value={chosen}
            onChange={(event) => setChosen(event.target.value)}
          >
            {model.lines.map((option) => (
              <option key={lineKey(option)} value={lineKey(option)}>
                {lineLabel(option)}
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

      <section className="mt-5" aria-labelledby="projection">
        <h3 id="projection" className="text-sm font-semibold">
          What the {line.minAge}+ line means for adults
        </h3>
        {line.adults.length === 0 ? (
          <p className="mt-1 text-sm text-ink-500">
            Not measured for the age model in use ({model.version}), so there is no projection.
          </p>
        ) : (
          <>
            <table className="mt-2 w-full text-left text-sm">
              <thead className="text-xs uppercase text-ink-500">
                <tr>
                  <th className="py-1.5 pr-3 font-medium">Adults aged</th>
                  <th className="py-1.5 pr-3 font-medium">Sent to a stronger check</th>
                  <th className="py-1.5 pr-3 font-medium">Pass</th>
                  <th className="py-1.5 font-medium">Turned away</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200 dark:divide-white/10">
                {line.adults.map((band) => (
                  <tr key={band.ages}>
                    <td className="py-1.5 pr-3 tabular-nums">{agesText(band.ages)}</td>
                    <td className="py-1.5 pr-3 font-medium tabular-nums">{percent(band.stepUp)}</td>
                    <td className="py-1.5 pr-3 tabular-nums">{percent(band.pass)}</td>
                    <td className="py-1.5 tabular-nums">{percent(band.fail)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs leading-relaxed text-ink-500">
              Measured once on {line.adults.reduce((sum, band) => sum + band.faces, 0).toLocaleString("en")}{" "}
              photos of adults{model.calibratedOn === null ? "" : ` from ${model.calibratedOn.name}`}, whose
              ages were estimated rather than documented. A projection, not a promise: your visitors, their
              cameras and their light will differ.
            </p>
          </>
        )}
      </section>
    </>
  );
}
