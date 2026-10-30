import { isOn, readVerifyLink, type VerifyLink } from "./link.js";
import { readMessage } from "./protocol.js";

/** How the check opens: in a modal over your page (the default), or by sending the whole page to it. */
export type Mode = "modal" | "redirect";

export interface Finished {
  sessionId: string;
  redirectUrl: string;
}

export interface OpenOptions {
  mode?: Mode;
  /** The check is over. By default the page goes to `redirectUrl`, where your server asks Dwarpal for the result —
   * never trust this callback alone: anyone can call it from the browser's console. */
  onFinished?: (finished: Finished) => void;
  /** The person closed the modal before the end. The session stays open until it expires. */
  onClose?: () => void;
}

/** An open check. `close` removes the modal (a redirect can't be taken back). */
export interface AgeCheck {
  close(): void;
}

/** Open the age check for a session's `url`, which your server got when it created the session. */
export function openAgeCheck(url: string, options: OpenOptions = {}): AgeCheck {
  const link = readVerifyLink(url);
  if (options.mode === "redirect") {
    window.location.assign(link.url);
    return { close() {} };
  }
  return openModal(link, options);
}

function openModal(link: VerifyLink, options: OpenOptions): AgeCheck {
  const before = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  const overlay = document.createElement("div");
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Age check");
  Object.assign(overlay.style, {
    position: "fixed",
    inset: "0",
    zIndex: "2147483647",
    display: "grid",
    placeItems: "center",
    padding: "16px",
    background: "rgba(12, 10, 9, 0.72)",
  });

  const frame = document.createElement("iframe");
  frame.src = link.url;
  frame.title = "Age check";
  frame.allow = "camera; fullscreen";
  Object.assign(frame.style, {
    width: "min(480px, 100%)",
    height: "min(760px, 100%)",
    border: "0",
    borderRadius: "16px",
    background: "#ffffff",
    boxShadow: "0 24px 64px rgba(0, 0, 0, 0.45)",
  });

  const closer = document.createElement("button");
  closer.type = "button";
  closer.textContent = "Close";
  closer.setAttribute("aria-label", "Close the age check");
  Object.assign(closer.style, {
    position: "absolute",
    top: "12px",
    right: "12px",
    minHeight: "44px",
    padding: "0 16px",
    border: "0",
    borderRadius: "999px",
    background: "#ffffff",
    color: "#1c1917",
    font: "600 14px/1 system-ui, sans-serif",
    cursor: "pointer",
  });

  overlay.append(frame, closer);
  document.body.append(overlay);
  closer.focus();

  let open = true;
  const remove = () => {
    if (!open) {
      return false;
    }
    open = false;
    window.removeEventListener("message", onMessage);
    document.removeEventListener("keydown", onKey);
    overlay.remove();
    before?.focus();
    return true;
  };
  const close = () => {
    if (remove()) {
      options.onClose?.();
    }
  };

  function onMessage(event: MessageEvent) {
    // Only the frame this modal opened, at the verify page's origin, about this session.
    if (event.source !== frame.contentWindow || event.origin !== link.origin) {
      return;
    }
    const message = readMessage(event.data);
    if (message === null || message.sessionId !== link.sessionId) {
      return;
    }
    if (message.type === "full_page") {
      remove();
      window.location.assign(link.url);
    } else if (isOn(message.redirectUrl, window.location.origin)) {
      remove();
      const finished = { sessionId: message.sessionId, redirectUrl: message.redirectUrl };
      (options.onFinished ?? ((done: Finished) => window.location.assign(done.redirectUrl)))(finished);
    }
  }

  function onKey(event: KeyboardEvent) {
    if (event.key === "Escape") {
      close();
    }
  }

  closer.addEventListener("click", close);
  window.addEventListener("message", onMessage);
  document.addEventListener("keydown", onKey);
  return { close };
}
