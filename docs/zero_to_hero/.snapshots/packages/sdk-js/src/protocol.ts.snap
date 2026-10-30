/**
 * What the verify page, inside a website's frame, may tell that website — the only messages either side acts on.
 * The verify page sends each one with `postMessage` to the website's origin alone; the website accepts it only from
 * the frame it opened, at the verify page's origin (`open.ts`).
 */

export const MESSAGE_SOURCE = "dwarpal";

/** The check is over: send the person to `redirectUrl`, the website's own return address with the session's ID. */
export interface FinishedMessage {
  source: typeof MESSAGE_SOURCE;
  type: "finished";
  sessionId: string;
  redirectUrl: string;
}

/** The check can't go on inside the frame (a camera the browser won't share with frames, say): open it full-page. */
export interface FullPageMessage {
  source: typeof MESSAGE_SOURCE;
  type: "full_page";
  sessionId: string;
}

export type VerifyMessage = FinishedMessage | FullPageMessage;

export const SESSION_ID = /^vs_[0-9A-Za-z]{26}$/;

type Fields = Record<string, unknown>;

function isWebAddress(text: unknown): text is string {
  if (typeof text !== "string") {
    return false;
  }
  try {
    const url = new URL(text);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

/** A message read from `event.data`, if it is one of ours and well formed; anything else is `null`, and ignored. */
export function readMessage(data: unknown): VerifyMessage | null {
  if (typeof data !== "object" || data === null) {
    return null;
  }
  const message = data as Fields;
  if (message.source !== MESSAGE_SOURCE || typeof message.sessionId !== "string") {
    return null;
  }
  if (!SESSION_ID.test(message.sessionId)) {
    return null;
  }
  if (message.type === "finished" && isWebAddress(message.redirectUrl)) {
    return {
      source: MESSAGE_SOURCE,
      type: "finished",
      sessionId: message.sessionId,
      redirectUrl: message.redirectUrl,
    };
  }
  if (message.type === "full_page") {
    return { source: MESSAGE_SOURCE, type: "full_page", sessionId: message.sessionId };
  }
  return null;
}
