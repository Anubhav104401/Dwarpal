import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import { getLocale } from "next-intl/server";
import type { ReactNode } from "react";

// Noto Sans Devanagari (decision D2b), served from this site: Geist has no Devanagari letters, so the Hindi pages
// borrow them from it. Each of its faces is fetched only when a page shows a letter in that face's range.
import "@fontsource-variable/noto-sans-devanagari";
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

export default async function RootLayout({ children }: { children: ReactNode }) {
  // Reading the request makes every page render per request, so each gets the nonce of its own policy (proxy.ts).
  await headers();
  // The page's language (decision D2), so screen readers pronounce it and browsers pick the right fonts.
  const locale = await getLocale();
  return (
    <html lang={locale} className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="min-h-dvh bg-ink-50 font-sans text-ink-900 antialiased dark:bg-ink-950 dark:text-ink-100">
        {children}
      </body>
    </html>
  );
}
