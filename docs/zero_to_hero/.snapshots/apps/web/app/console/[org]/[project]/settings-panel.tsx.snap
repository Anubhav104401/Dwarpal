"use client";

import { type FormEvent, useState } from "react";

import { Alert, Field, input, panel, smallButton } from "@/components/console-shell";
import { type ConsoleClient, ConsoleError, type Project } from "@/lib/console-api";
import { originLines } from "@/lib/origins";

type Props = {
  client: ConsoleClient;
  org: string;
  project: Project;
  canChange: boolean;
  onSaved: () => Promise<void>;
};

/** A project's name and the origins its websites run on (decisions D28, D29): a check may only return to one of them,
 * and only they may show the verify page in a frame. Owners and admins may change them. */
export function SettingsPanel({ client, org, project, canChange, onSaved }: Props) {
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setError(null);
    setSaved(false);
    try {
      await client.updateProject(org, project.id, {
        name: String(data.get("name") ?? "").trim(),
        allowedOrigins: originLines(String(data.get("origins") ?? "")),
      });
      await onSaved();
      setSaved(true);
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  return (
    <section className={`${panel} mt-6`} aria-labelledby="settings">
      <h2 id="settings" className="text-lg font-semibold">
        Settings
      </h2>
      <p className="mt-1 text-sm text-ink-500">
        A check may only return to these origins, and only they may show the verify page in a frame. An origin
        is just <code>https://</code> and a host name, with a port if it isn't the usual one.
      </p>
      {error === null ? null : (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}
      {canChange ? (
        // Keyed by what is stored, so after a save the form shows the origins as the API wrote them.
        <form
          key={`${project.name}\n${project.allowedOrigins.join("\n")}`}
          className="mt-4 space-y-3"
          onSubmit={save}
        >
          <Field label="Name" id="project-name">
            <input
              id="project-name"
              className={input}
              name="name"
              required
              maxLength={80}
              defaultValue={project.name}
            />
          </Field>
          <Field label="Allowed origins, one per line" id="project-origins">
            <textarea
              id="project-origins"
              className={`${input} min-h-24 font-mono`}
              name="origins"
              placeholder="https://shop.example"
              defaultValue={project.allowedOrigins.join("\n")}
            />
          </Field>
          <div className="flex items-center gap-3">
            <button type="submit" className={smallButton}>
              Save
            </button>
            {saved ? (
              <span className="text-sm text-ink-500" role="status">
                Saved.
              </span>
            ) : null}
          </div>
        </form>
      ) : project.allowedOrigins.length === 0 ? (
        <p className="mt-3 text-sm text-ink-500">No allowed origins yet.</p>
      ) : (
        <ul className="mt-3 space-y-1 font-mono text-xs">
          {project.allowedOrigins.map((origin) => (
            <li key={origin}>{origin}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
