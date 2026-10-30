"use client";

import { VerifyAgeButton } from "@dwarpal/react";
import type { ReactNode } from "react";

import { button } from "@/components/ui";

import { createAgeCheck } from "./actions";

/**
 * The shop's age-check button: our server creates the session (with our secret key, never in the browser), and
 * Dwarpal's check opens in a modal over this page. At the end the page goes to our return address, where our server
 * asks Dwarpal for the result — the browser is never trusted with it.
 */
export function AgeCheckButton({ children }: { children: ReactNode }) {
  return (
    <VerifyAgeButton
      createSession={createAgeCheck}
      onError={() => window.location.assign("/refused?reason=error")}
      className={button}
    >
      {children}
    </VerifyAgeButton>
  );
}
