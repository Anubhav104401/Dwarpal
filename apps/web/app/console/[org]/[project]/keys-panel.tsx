"use client";

import { useCallback, useEffect, useState } from "react";

import { Alert, panel, quietButton } from "@/components/console-shell";
import { Badge } from "@/components/ui";
import { type ApiKeyInfo, type ConsoleClient, ConsoleError } from "@/lib/console-api";

type Props = { client: ConsoleClient; org: string; project: string };

const TONES = { expired: "neutral", revoked: "danger" } as const;

/** A project's API keys (decision D30): when each was made, what it may do, its mode — never its secret, which Dwarpal
 * doesn't keep — and a button to stop one at once. New keys are made on the organisation's page. */
export function KeysPanel({ client, org, project }: Props) {
  const [keys, setKeys] = useState<ApiKeyInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setKeys(await client.keys(org, project));
  }, [client, org, project]);

  useEffect(() => {
    load().catch(() => setError("The console couldn't load the keys. Please try again."));
  }, [load]);

  async function revoke(key: string) {
    if (!window.confirm(`Stop the key ${key} now? Anything still using it will be refused.`)) return;
    setError(null);
    try {
      await client.revokeKey(org, project, key);
      await load();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  return (
    <section className={`${panel} mt-6`} aria-labelledby="keys">
      <h2 id="keys" className="text-lg font-semibold">
        API keys
      </h2>
      <p className="mt-1 text-sm text-ink-500">
        A key's secret is shown once, when it is made. If one may have leaked, stop it here and make a new
        one.
      </p>
      {error === null ? null : (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}
      {keys === null ? (
        <p className="mt-3 text-sm text-ink-500">Loading…</p>
      ) : keys.length === 0 ? (
        <p className="mt-3 text-sm text-ink-500">No keys yet.</p>
      ) : (
        <table className="mt-3 w-full text-left text-sm">
          <thead className="text-xs uppercase text-ink-500">
            <tr>
              <th className="py-2 pr-3 font-medium">Key</th>
              <th className="py-2 pr-3 font-medium">Mode</th>
              <th className="py-2 pr-3 font-medium">Scopes</th>
              <th className="py-2 pr-3 font-medium">Made</th>
              <th className="py-2 font-medium">
                <span className="sr-only">State</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-200 dark:divide-white/10">
            {keys.map((k) => (
              <tr key={k.id}>
                <td className="py-2 pr-3">
                  <code className="text-xs">{k.id}</code>
                </td>
                <td className="py-2 pr-3">{k.livemode ? "Live" : "Test"}</td>
                <td className="py-2 pr-3 text-xs">{k.scopes.join(", ")}</td>
                <td className="py-2 pr-3 tabular-nums">{new Date(k.createdAt).toLocaleDateString()}</td>
                <td className="py-2 text-right">
                  {k.state === "active" ? (
                    <button
                      type="button"
                      className={quietButton}
                      aria-label={`Stop key ${k.id}`}
                      onClick={() => revoke(k.id)}
                    >
                      Stop
                    </button>
                  ) : (
                    <Badge tone={TONES[k.state]}>{k.state === "revoked" ? "Stopped" : "Expired"}</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
