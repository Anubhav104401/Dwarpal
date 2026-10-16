import { GeistSans } from "geist/font/sans";
import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Amber Cellars · Small-batch wines",
  description: "A demo shop that checks its visitors' age with Dwarpal.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={GeistSans.variable}>
      <body className="min-h-dvh bg-stone-950 font-sans text-stone-100 antialiased">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(70%_50%_at_50%_0%,color-mix(in_oklab,var(--color-wine-500)_35%,transparent),transparent)]" />
        <header className="relative mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
          <Link href="/" className="font-serif text-xl tracking-wide text-amber-glow">
            Amber Cellars
          </Link>
          <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-stone-400">
            Demo shop · not a real store
          </span>
        </header>
        <main className="relative mx-auto max-w-5xl px-6 pb-20">{children}</main>
      </body>
    </html>
  );
}
