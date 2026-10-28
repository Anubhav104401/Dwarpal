"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { Alert, Field, input, panel, quietButton, smallButton } from "@/components/console-shell";
import { Badge } from "@/components/ui";
import {
  type ConsoleClient,
  ConsoleError,
  type Delivery,
  EVENT_TYPES,
  type WebhookEndpoint,
} from "@/lib/console-api";

type Props = { client: ConsoleClient; org: string; project: string; livemode: boolean };

/** A project's webhook endpoints for one mode: add one (its secret shown once), send a test, see and replay deliveries. */
export function WebhooksPanel({ client, org, project, livemode }: Props) {
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[] | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [shown, setShown] = useState<{ endpoint: string; deliveries: Delivery[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setEndpoints(await client.webhooks(org, project, livemode));
  }, [client, org, project, livemode]);

  useEffect(() => {
    setSecret(null);
    setShown(null);
    load().catch(() => setError("The console couldn't load the webhooks. Please try again."));
  }, [load]);

  async function attempt(work: () => Promise<void>) {
    setError(null);
    try {
      await work();
    } catch (failure) {
      setError(failure instanceof ConsoleError ? failure.message : "That didn't work. Please try again.");
    }
  }

  async function showDeliveries(endpoint: string) {
    setShown({ endpoint, deliveries: await client.deliveries(org, project, livemode, endpoint) });
  }

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    await attempt(async () => {
      const events = data.getAll("events").map(String);
      const created = await client.addWebhook(org, project, livemode, String(data.get("url")), events);
      form.reset();
      setSecret(created.secret);
      await load();
    });
  }

  const sendTest = (endpoint: string) =>
    attempt(async () => {
      await client.testWebhook(org, project, livemode, endpoint);
      await showDeliveries(endpoint);
    });

  const switchTo = (endpoint: string, enabled: boolean) =>
    attempt(async () => {
      await client.switchWebhook(org, project, livemode, endpoint, enabled);
      await load();
    });

  const remove = (endpoint: string) =>
    attempt(async () => {
      await client.removeWebhook(org, project, livemode, endpoint);
      if (shown?.endpoint === endpoint) setShown(null);
      await load();
    });

  const replay = (endpoint: string, delivery: string) =>
    attempt(async () => {
      await client.replay(org, project, livemode, delivery);
      await showDeliveries(endpoint);
    });

  return (
    <section className={`${panel} mt-6`} aria-labelledby="webhooks">
      <h2 id="webhooks" className="text-lg font-semibold">
        Webhooks
      </h2>
      <p className="mt-1 text-sm text-ink-500">
        Addresses Dwarpal tells when a {livemode ? "live" : "test"} session finishes or expires. Every request
        is signed with the endpoint's secret.
      </p>
      {error === null ? null : (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}
      {secret === null ? null : (
        <div className="mt-4 rounded-xl border border-brand-500/40 bg-brand-500/10 p-3 text-sm" role="status">
          <p className="font-semibold">
            The endpoint's signing secret — copy it now. It won't be shown again.
          </p>
          <code className="mt-2 block break-all" data-testid="new-secret">
            {secret}
          </code>
        </div>
      )}

      {endpoints === null ? (
        <p className="mt-3 text-sm text-ink-500">Loading…</p>
      ) : endpoints.length === 0 ? (
        <p className="mt-3 text-sm text-ink-500">No endpoints yet.</p>
      ) : (
        <ul className="mt-3 divide-y divide-ink-200 dark:divide-white/10">
          {endpoints.map((e) => (
            <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <div className="min-w-0">
                <p className="break-all font-mono text-xs">
                  {e.url} {e.enabled ? null : <Badge tone="neutral">Off</Badge>}
                </p>
                <p className="text-xs text-ink-500">{e.events.join(", ")}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" className={quietButton} onClick={() => sendTest(e.id)}>
                  Send test
                </button>
                <button
                  type="button"
                  className={quietButton}
                  onClick={() => attempt(() => showDeliveries(e.id))}
                >
                  Deliveries
                </button>
                <button type="button" className={quietButton} onClick={() => switchTo(e.id, !e.enabled)}>
                  {e.enabled ? "Switch off" : "Switch on"}
                </button>
                <button type="button" className={quietButton} onClick={() => remove(e.id)}>
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {shown === null ? null : (
        <div className="mt-4" aria-live="polite">
          <h3 className="text-sm font-semibold">Recent deliveries</h3>
          {shown.deliveries.length === 0 ? (
            <p className="mt-1 text-sm text-ink-500">None yet.</p>
          ) : (
            <table className="mt-2 w-full text-left text-sm" aria-label="Recent deliveries">
              <thead className="text-xs uppercase text-ink-500">
                <tr>
                  <th className="py-2 pr-3 font-medium">Created</th>
                  <th className="py-2 pr-3 font-medium">Status</th>
                  <th className="py-2 pr-3 font-medium">Tries</th>
                  <th className="py-2 pr-3 font-medium">Last answer</th>
                  <th className="py-2 font-medium">
                    <span className="sr-only">Replay</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-200 dark:divide-white/10">
                {shown.deliveries.map((d) => (
                  <tr key={d.id}>
                    <td className="py-2 pr-3 tabular-nums">{new Date(d.createdAt).toLocaleString()}</td>
                    <td className="py-2 pr-3">{d.status}</td>
                    <td className="py-2 pr-3 tabular-nums">{d.attempt}</td>
                    <td className="py-2 pr-3">{d.lastStatus ?? d.lastError ?? "—"}</td>
                    <td className="py-2 text-right">
                      {d.status === "pending" ? null : (
                        <button
                          type="button"
                          className={quietButton}
                          onClick={() => replay(shown.endpoint, d.id)}
                        >
                          Replay
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <form className="mt-4 space-y-3" onSubmit={add}>
        <Field label="Endpoint URL" id="webhook-url">
          <input
            id="webhook-url"
            className={input}
            name="url"
            type="url"
            required
            placeholder="https://shop.example/dwarpal-events"
          />
        </Field>
        <fieldset>
          <legend className="text-sm font-medium text-ink-700 dark:text-ink-300">Events</legend>
          {EVENT_TYPES.map((type) => (
            <label key={type} className="flex min-h-8 items-center gap-2 text-sm">
              <input type="checkbox" className="size-4" name="events" value={type} defaultChecked />
              <code className="text-xs">{type}</code>
            </label>
          ))}
        </fieldset>
        <button type="submit" className={smallButton}>
          Add endpoint
        </button>
      </form>
    </section>
  );
}
