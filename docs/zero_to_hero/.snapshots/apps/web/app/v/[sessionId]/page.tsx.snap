import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { VerifyFlow } from "./verify-flow";

export const metadata: Metadata = { title: "Confirm your age · Dwarpal" };

const SESSION_ID = /^vs_[0-9A-Za-z]{26}$/;

export default async function VerifyPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await params;
  if (!SESSION_ID.test(sessionId)) {
    notFound();
  }
  return (
    <VerifyFlow
      sessionId={sessionId}
      apiUrl={process.env.NEXT_PUBLIC_DWARPAL_API_URL ?? "http://localhost:8000"}
    />
  );
}
