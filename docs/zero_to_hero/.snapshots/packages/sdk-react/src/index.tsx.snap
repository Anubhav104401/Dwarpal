"use client";

import { type AgeCheck, type OpenOptions, openAgeCheck } from "@dwarpal/js";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";

export type { Finished, Mode, OpenOptions } from "@dwarpal/js";

/** Open age checks from a component. Opening a new one closes the last; leaving the page closes any still open. */
export function useDwarpal(): { open: (url: string, options?: OpenOptions) => AgeCheck } {
  const current = useRef<AgeCheck | null>(null);
  useEffect(() => () => current.current?.close(), []);
  const open = useCallback((url: string, options?: OpenOptions) => {
    current.current?.close();
    current.current = openAgeCheck(url, options);
    return current.current;
  }, []);
  return { open };
}

export interface VerifyAgeButtonProps extends OpenOptions {
  /** Ask *your server* for a new session, and return its `url`. Sessions are never created in the browser: that
   * needs your secret key. */
  createSession: () => Promise<string>;
  /** Creating the session failed (your server's error, or a link that isn't a verify link). */
  onError?: (error: unknown) => void;
  className?: string;
  children?: ReactNode;
}

/** A button that creates a session through your server and opens its age check. */
export function VerifyAgeButton({
  createSession,
  onError,
  className,
  children = "Verify my age",
  ...options
}: VerifyAgeButtonProps) {
  const { open } = useDwarpal();
  const [busy, setBusy] = useState(false);

  async function start() {
    if (busy) {
      return;
    }
    setBusy(true);
    try {
      open(await createSession(), options);
    } catch (error) {
      onError?.(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    // Not `disabled` while busy: a disabled button loses the keyboard focus, which the modal gives back on closing.
    <button type="button" className={className} aria-disabled={busy} aria-busy={busy} onClick={start}>
      {children}
    </button>
  );
}
