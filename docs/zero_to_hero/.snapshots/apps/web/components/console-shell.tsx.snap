import type { ReactNode } from "react";

import { Mark } from "./shell";
import { Badge, button } from "./ui";

// The console's pieces, from the design system; the pages import them from here.
export { Alert, Field, input, panel } from "./ui";
export const smallButton = button("primary", "small");
export const quietButton = button("quiet", "compact");

/** The console's frame: wider than the verify page, with who is signed in and a way out. */
export function ConsoleShell({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="mx-auto flex min-h-dvh max-w-5xl flex-col px-4 py-6 sm:px-6">
      <header className="flex items-center gap-2.5 border-b border-ink-200 pb-4 dark:border-white/10">
        <Mark />
        <span className="text-[15px] font-semibold tracking-tight">Dwarpal</span>
        <Badge tone="brand">Console</Badge>
        <div className="ml-auto flex items-center gap-2 text-sm">{aside}</div>
      </header>
      <main className="flex-1 py-8">{children}</main>
    </div>
  );
}
