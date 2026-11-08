import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";

import { VerifyFlow } from "./verify-flow";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getTranslations("Verify"))("metaTitle") };
}

/** The groups of words (`messages/`) the verify page uses in the browser: only these travel with it (decision D2). */
const IN_BROWSER = new Set(["Verify", "Camera", "DocumentCamera", "Tips", "Problems", "Shell", "Language"]);

const SESSION_ID = /^vs_[0-9A-Za-z]{26}$/;

export default async function VerifyPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  if (!SESSION_ID.test(sessionId)) {
    notFound();
  }
  const messages = await getMessages();
  const forBrowser = Object.fromEntries(Object.entries(messages).filter(([name]) => IN_BROWSER.has(name)));
  return (
    <NextIntlClientProvider messages={forBrowser}>
      <VerifyFlow
        sessionId={sessionId}
        apiUrl={process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000"}
      />
    </NextIntlClientProvider>
  );
}
