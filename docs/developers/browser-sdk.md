# Browser SDKs: `@dwarpal/js` and `@dwarpal/react`

The browser SDKs open Dwarpal's age check on your website's page. They hold no keys and see no results: your server creates the session and checks the result. See [Integrating Dwarpal](README.md) for the whole flow.

- **`@dwarpal/js`** — for any web page. No dependencies.
- **`@dwarpal/react`** — a button and a hook for React 19 websites, built on `@dwarpal/js`.

## `openAgeCheck(url, options?)`

```ts
import { openAgeCheck } from "@dwarpal/js";

const check = openAgeCheck(session.url, {
  mode: "modal", // or "redirect"
  onFinished: ({ sessionId, redirectUrl }) => window.location.assign(redirectUrl),
  onClose: () => console.log("closed before the end"),
});
check.close(); // takes the modal away
```

`url` is the session's verify link, exactly as your server got it from `createSession`. The SDK checks it first and throws a `TypeError` for anything else: it must be a `/v/vs_…` page with its `#cs=` secret, over HTTPS (plain HTTP only on `localhost`).

| Option | Default | Meaning |
| :-- | :-- | :-- |
| `mode` | `"modal"` | `"modal"` opens the check in a frame over your page; `"redirect"` sends the whole page to it |
| `onFinished` | go to `redirectUrl` | the check is over; `redirectUrl` is your return address with `?session_id=vs_…` |
| `onClose` | — | the person closed the modal before the end; the session stays open until it expires |

`onFinished` proves nothing on its own — anyone can call a function in their own browser. Let people in only after your server has verified the age token.

### The modal

- A dialog (`role="dialog"`, `aria-modal`) named "Age check", over a dimmed page, with a **Close** button that takes the keyboard focus. Escape closes it too. On closing, the focus returns to whatever had it before.
- The verify page sits in an `<iframe allow="camera; fullscreen">`, at most 480 × 760 pixels and never larger than the window.
- Its styles are set from script, so your content security policy needs no `style-src` change.

### What your page needs to allow

- **Framing.** The verify page allows itself to be framed only by the origin of the session's return address, and that origin must be one of your project's allowed origins. So open the check from a page on the same origin as your return address.
- **Camera.** If your page sends a `Permissions-Policy` header, it must allow the camera for the verify page's origin, for example `camera=(self "https://verify.dwarpal.example")`. With no such header, browsers allow it.
- **Content security policy.** If your page has one, `frame-src` (or `child-src`, or `default-src`) must allow the verify page's origin.

### Messages between the verify page and your page

The verify page talks to your page only with `postMessage`, and only to the origin of the session's return address. The SDK accepts a message only from the frame it opened, at the verify page's origin, about its own session. There are two messages:

| Message | Sent when | The SDK |
| :-- | :-- | :-- |
| `finished` | the person pressed *Continue* | closes the modal and calls `onFinished`, if `redirectUrl` is on your own origin (otherwise it ignores the message) |
| `full_page` | the check can't go on in a frame (a browser that won't share the camera with frames) | closes the modal and sends the whole page to the verify link |

Neither message carries a result.

## `@dwarpal/react`

### `<VerifyAgeButton>`

```tsx
"use client";

import { VerifyAgeButton } from "@dwarpal/react";

import { createAgeCheck } from "./actions"; // a server action returning session.url

export function AgeCheckButton() {
  return (
    <VerifyAgeButton
      createSession={createAgeCheck}
      onError={() => window.location.assign("/age-check/failed")}
      className="button"
    >
      Verify my age to enter
    </VerifyAgeButton>
  );
}
```

| Prop | Meaning |
| :-- | :-- |
| `createSession` | **required**: asks your server for a new session and returns its `url` |
| `onError` | creating the session failed, or the link wasn't a verify link |
| `className`, `children` | your style and words (default: "Verify my age") |
| `mode`, `onFinished`, `onClose` | as for `openAgeCheck` |

While the session is being created the button is marked `aria-busy` and `aria-disabled`, and ignores further presses. It isn't `disabled`, so it keeps the keyboard focus, which the modal returns to it on closing.

### `useDwarpal()`

```tsx
const { open } = useDwarpal();
// later, with a session's url from your server:
open(url, { onClose: () => setChecking(false) });
```

`open` takes the same arguments as `openAgeCheck`. Opening a new check closes the previous one, and a check still open closes when the component goes away.
