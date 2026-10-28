"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";

import { ConsoleClient } from "@/lib/console-api";
import { matching, PLACES, type Place } from "@/lib/places";

import { input } from "./ui";

const client = new ConsoleClient();

/** The fixed places, then every organisation the person belongs to and each of its projects. */
async function everyPlace(): Promise<Place[]> {
  const me = await client.me();
  if (me === null) return PLACES;
  const found = await Promise.all(
    me.organisations.map(async (org) => {
      const projects = await client.projects(org.id).catch(() => []);
      return [
        { label: org.name, href: `/console/${org.id}`, hint: "Organisation" },
        ...projects.map((p) => ({
          label: p.name,
          href: `/console/${org.id}/${p.id}`,
          hint: `Project in ${org.name}`,
        })),
      ];
    }),
  );
  return [...PLACES, ...found.flat()];
}

/** A search box over the console's places, in a modal dialog: type to narrow, Enter to go to the first, or arrow
 *  down into the list. A native <dialog> keeps focus inside it and closes on Escape. */
export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const [places, setPlaces] = useState<Place[]>(PLACES);
  const [typed, setTyped] = useState("");
  const router = useRouter();
  const shown = matching(places, typed);

  useEffect(() => {
    const box = dialog.current;
    if (!box) return;
    if (open && !box.open) {
      setTyped("");
      box.showModal();
      everyPlace()
        .then(setPlaces)
        .catch(() => setPlaces(PLACES));
    } else if (!open && box.open) {
      box.close();
    }
  }, [open]);

  function go(place: Place | undefined) {
    if (!place) return;
    onClose();
    router.push(place.href);
  }

  function fromBox(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      go(shown[0]);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      list.current?.querySelector("a")?.focus();
    }
  }

  function withinList(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    event.preventDefault();
    const links = [...(list.current?.querySelectorAll("a") ?? [])];
    const here = links.indexOf(document.activeElement as HTMLAnchorElement);
    const next = here + (event.key === "ArrowDown" ? 1 : -1);
    if (next < 0) dialog.current?.querySelector("input")?.focus();
    else links[Math.min(next, links.length - 1)]?.focus();
  }

  return (
    <dialog
      ref={dialog}
      aria-label="Go to"
      onClose={onClose}
      className="m-auto mt-[15vh] w-[min(36rem,calc(100vw-2rem))] rounded-2xl border border-ink-200 bg-white p-0 text-ink-900 shadow-xl backdrop:bg-ink-950/40 dark:border-white/10 dark:bg-ink-900 dark:text-ink-50"
    >
      <div className="border-b border-ink-200 p-3 dark:border-white/10">
        <input
          type="search"
          className={input}
          aria-label="Search the console"
          placeholder="Search organisations, projects and pages"
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          onKeyDown={fromBox}
        />
      </div>
      {shown.length === 0 ? (
        <p className="p-4 text-sm text-ink-500">Nothing matches.</p>
      ) : (
        <ul ref={list} aria-label="Results" className="max-h-80 overflow-y-auto p-2" onKeyDown={withinList}>
          {shown.map((place) => (
            <li key={place.href}>
              <Link
                href={place.href}
                onClick={onClose}
                className="flex items-baseline justify-between gap-3 rounded-lg px-3 py-2 text-sm hover:bg-ink-100 focus:bg-ink-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-600 dark:hover:bg-white/5 dark:focus:bg-white/5"
              >
                <span className="font-medium">{place.label}</span>
                <span className="truncate text-xs text-ink-500">{place.hint}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </dialog>
  );
}
