import { SESSION_ID } from "./protocol.js";

/** A verify link, checked: the whole link, the verify page's origin, and the session's ID. */
export interface VerifyLink {
  url: string;
  origin: string;
  sessionId: string;
}

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

/**
 * Check a session's `url`, as your server got it from Dwarpal, before opening it: a verify page (`/v/vs_…`) with its
 * one-time secret in the `#cs=` fragment, over HTTPS (plain HTTP only on this computer, for development).
 */
export function readVerifyLink(text: string): VerifyLink {
  let url: URL;
  try {
    url = new URL(text);
  } catch {
    throw new TypeError("not a verify link: not a web address");
  }
  if (url.protocol !== "https:" && !(url.protocol === "http:" && LOCAL_HOSTS.has(url.hostname))) {
    throw new TypeError("not a verify link: it must use https");
  }
  const sessionId = /^\/v\/([^/]+)$/.exec(url.pathname)?.[1] ?? "";
  if (!SESSION_ID.test(sessionId)) {
    throw new TypeError("not a verify link: no session in its path");
  }
  if (!new URLSearchParams(url.hash.slice(1)).get("cs")) {
    throw new TypeError("not a verify link: its secret (#cs=) is missing");
  }
  return { url: url.href, origin: url.origin, sessionId };
}

/** Whether `text` is an address on `origin` — the website's own — so a message can't send the person elsewhere. */
export function isOn(text: string, origin: string): boolean {
  try {
    return new URL(text).origin === origin;
  } catch {
    return false;
  }
}
