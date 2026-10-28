"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { PLACES } from "@/lib/places";

import { CommandPalette } from "./command-palette";
import { Mark } from "./shell";
import { Badge, button } from "./ui";

// The console's pieces, from the design system; the pages import them from here.
export { Alert, Field, input, panel } from "./ui";
export const smallButton = button("primary", "small");
export const quietButton = button("quiet", "compact");

/** The console's frame: wider than the verify page, with who is signed in and a way out. Signed in, it adds the
 *  sidebar of places — a row above the page on narrow screens — and the command palette, on ⌘K or Ctrl+K. */
export function ConsoleShell({
  children,
  aside,
  signedIn = false,
}: {
  children: ReactNode;
  aside?: ReactNode;
  signedIn?: boolean;
}) {
  const here = usePathname();
  const [palette, setPalette] = useState(false);
  const [keys, setKeys] = useState("Ctrl K"); // ⌘K on a Mac, found once the page is in the browser

  useEffect(() => {
    if (/Mac|iPhone|iPad/.test(navigator.userAgent)) setKeys("⌘K");
  }, []);

  useEffect(() => {
    if (!signedIn) return;
    const open = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPalette(true);
      }
    };
    window.addEventListener("keydown", open);
    return () => window.removeEventListener("keydown", open);
  }, [signedIn]);

  return (
    <div className="mx-auto flex min-h-dvh max-w-6xl flex-col px-4 py-6 sm:px-6">
      <header className="flex items-center gap-2.5 border-b border-ink-200 pb-4 dark:border-white/10">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        <Badge tone="brand">Console</Badge>
        <div className="ml-auto flex items-center gap-2 text-sm">{aside}</div>
      </header>
      <div className={signedIn ? "flex-1 lg:grid lg:grid-cols-[12rem_1fr] lg:gap-8" : "flex-1"}>
        {signedIn && (
          <nav aria-label="Console" className="pt-4 lg:pt-8">
            <button
              type="button"
              className="mb-3 flex w-full items-center justify-between rounded-lg border border-ink-200 px-3 py-1.5 text-sm text-ink-500 hover:border-ink-300 dark:border-white/10 dark:hover:border-white/20"
              onClick={() => setPalette(true)}
            >
              Go to…
              <kbd className="font-sans text-xs">{keys}</kbd>
            </button>
            <ul className="flex gap-1 overflow-x-auto lg:flex-col">
              {PLACES.map((place) => (
                <li key={place.href}>
                  <Link
                    href={place.href}
                    aria-current={here === place.href ? "page" : undefined}
                    className="block whitespace-nowrap rounded-lg px-3 py-1.5 text-sm text-ink-600 hover:bg-ink-100 aria-[current=page]:bg-ink-100 aria-[current=page]:font-semibold aria-[current=page]:text-ink-900 dark:text-ink-300 dark:hover:bg-white/5 dark:aria-[current=page]:bg-white/10 dark:aria-[current=page]:text-white"
                  >
                    {place.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
        <main className="min-w-0 py-8">{children}</main>
      </div>
      {signedIn && <CommandPalette open={palette} onClose={() => setPalette(false)} />}
    </div>
  );
}
