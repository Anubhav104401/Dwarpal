import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Dwarpal · Age check",
  description: "A quick, private age check. Your photos are checked once and never stored.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafafb" }, // ink-50
    { media: "(prefers-color-scheme: dark)", color: "#070814" }, // ink-950
  ],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="min-h-dvh bg-ink-50 font-sans text-ink-900 antialiased dark:bg-ink-950 dark:text-ink-100">
        {children}
      </body>
    </html>
  );
}
