---
fingerprint: 8652fcb942463696
---
The **React SDK**: a hook, `useDwarpal`, and a button, `VerifyAgeButton`. Both wrap `openAgeCheck` from `@dwarpal/js`.

@@ 1
`"use client"` — for websites built with Next.js (as the demo shop is): these pieces run in the browser, where the modal is, never on the server.

@@ 3-4
From the browser SDK: the opener and its types. From React: the type of anything that can be drawn (`ReactNode`), and four **hooks** — React's functions for keeping things between drawings of a component (§5.4).

@@ 6
Pass the browser SDK's option types on, so a website needs only this package.

@@ 8-9
**`useDwarpal`** — a **custom hook** (a function whose name starts with `use`, which may use React's hooks). It gives a component a way to `open` a check.

@@ 10
`useRef` — a box that keeps the check that is open, between drawings, without causing a new drawing when it changes.

@@ 11
`useEffect` with an empty list runs once, when the component appears; the function it *returns* runs when the component goes away. So leaving the page (or the component) closes a modal still open.

@@ 12-16
`open` — close any check this component already opened, open the new one, and keep it. `useCallback` with an empty list keeps the same function for the component's whole life, so components that receive it aren't redrawn for nothing.

@@ 17-18
The hook's answer.

@@ 20
**`VerifyAgeButtonProps`** — the button's options: everything `openAgeCheck` takes (`extends OpenOptions`), and:

@@ 21-23
`createSession` — a function that asks *the website's server* for a new session and returns its link. The component can't create sessions itself: that takes the secret key, which must never reach a browser.

@@ 24-25
`onError` — creating the session failed, or the link wasn't a verify link.

@@ 26-28
Its CSS class and its words — so each website styles it as its own.

@@ 30-37
**`VerifyAgeButton`**. Its options are taken apart in the brackets: the four of its own (with "Verify my age" as the default words), and `...options` — the rest — collected to pass on to the opener.

@@ 38-39
The hook, and whether the button is busy creating a session.

@@ 41-45
**`start`**, when pressed. While busy, a second press does nothing; otherwise, mark busy.

@@ 46-53
Ask the website's server for a session, and open its check. If anything fails, tell the website; either way, the button isn't busy any more (`finally`).

@@ 55-60
The button. It isn't **`disabled`** while busy: a disabled button loses the keyboard focus, and the modal could then not hand it back on closing (the browser test caught exactly this). Instead **`aria-disabled`** tells assistive technology it can't be used just now, and `start` ignores presses; `aria-busy` says it is working.

@@ 61
The end of the component.
