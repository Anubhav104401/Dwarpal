---
fingerprint: f250049288a3d01a
---
The console's **home** (Phase 5, §5.5.1): signing in, creating an account, and the list of a signed-in person's organisations. It runs in the browser (`"use client"`), because it holds what the person is typing and asks the API as they act.

The page has three states. While it asks the API who is signed in, it shows *Loading…*; if someone is, their organisations; if nobody is, the sign-in form, which can switch to creating an account. If the API says a one-time code is needed, the code field appears.

@@ 1
`"use client"`: this component runs in the browser, not on the server.

@@ 3-4
Next.js's `Link` (moves between pages without reloading), and React's form-event type and two hooks: `useEffect` (do something after showing) and `useState` (remember a value between showings).

@@ 6-14
The console's building blocks (`components/console-shell.tsx`).

@@ 15
The client, its error, and the `Me` type. Since 9 Nov also `waitInWords`, to say how long a lock lasts.

@@ 18
One client for the page. It keeps the CSRF token, so it must live as long as the page does.

@@ 20
The form's two modes.

@@ 22-23
**`explain`** — plain words for the refusals a person can do something about.

@@ 24
Anything that isn't a refusal from the API (the network failed, say) gets a general sentence.

@@ 25-36
The refusals by their stable code, each with a sentence that says what to do — since Phase 9 also an unknown passkey, and a sign-in that took too long. Since 9 Nov, too many sign-in attempts says how long to wait — from the answer's `Retry-After`, in words (`waitInWords`) — since a lock grows with each wrong try, up to an hour.

@@ 37
A code without its own sentence shows the API's own detail.

@@ 38
End of `explain`.

@@ 40-45
**`ConsoleHome`**, and what it remembers: who is signed in (`undefined` while unknown, `null` for nobody), the form's mode, whether the code field is needed, the current error, and whether a request is under way.

@@ 47-49
Once, when the page first appears, ask the API who is signed in. If that fails at all, treat it as nobody.

@@ 51-54
**`submit`** — the form was sent. `preventDefault` stops the browser's own submission (which would reload the page); `FormData` reads the fields by name.

@@ 55-56
Mark the request as under way (the button greys out), and clear the old error.

@@ 57-62
Sign in or sign up, and remember who that makes signed in. An empty code is sent as no code.

@@ 63-65
On a refusal, show the code field if the API asked for one, and show the explanation.

@@ 87-90
**`signOut`** — end the session and show the sign-in form again.

@@ 92-100
Still asking: show *Loading…* in a region screen readers announce politely.

@@ 102-114
**Signed in**: the frame, with its sidebar (`signedIn`), shows the person's address (on wider screens) and a *Sign out* button. The *Age model* and *Security* pages are in the sidebar (§5.5.6).

@@ 115
The heading.

@@ 116-128
Each organisation as a card linking to its page, with the person's role in it. Its border turns saffron on hover, with a short transition — only for people who haven't asked for reduced motion (`motion-safe:`).

@@ 129-131
End of the signed-in view.

@@ 133
**Nobody signed in**: which mode is the form in?

@@ 134-139
The frame, a card, and the heading for the mode.

@@ 140-142
A sentence that says who the console is for — and that people whose age is checked never need an account.

@@ 143
The form.

@@ 144-146
The e-mail field. `autoComplete="email"` lets the browser or a password manager fill it in.

@@ 147-157
The password. The `autoComplete` hint tells password managers whether to suggest a new one (signing up) or fill the saved one (signing in); signing up asks for 12 characters before the API would.

@@ 158-168
When signing up, the organisation's name.

@@ 169-184
When the API has asked for it, the code: `autoComplete="one-time-code"` lets phones offer a code they have just received; the pattern accepts six digits or a recovery code, and a hint underneath — tied to the field with `aria-describedby`, so screen readers read it too — says a recovery code works when the phone is lost.

@@ 185
The error, if there is one, announced to screen readers (`Alert`).

@@ 186-188
The submit button, disabled while a request is under way so it can't be sent twice.

@@ 189
End of the form.

@@ 200-209
A button that switches between signing in and creating an account, clearing any error from the other mode.

@@ 210-213
End of the card, the frame and the component.

@@ 16
The passkey helpers (Phase 9): whether a prompt was cancelled, whether passkeys work here, and the two translations a sign-in needs.

@@ 66-68
In every case, the request is no longer under way.

@@ 69
End of `submit`.

@@ 71-73
**`withPasskey`** (Phase 9) — sign in with a passkey. Mark the request under way and clear the old error.

@@ 74-79
Ask the API for a challenge; hand it to the browser, which shows the person their passkeys for this site and asks their device to verify them; send the device's answer back, and remember who that signs in.

@@ 80-81
A failure is explained — unless the person simply closed the prompt.

@@ 82-85
In every case, the request is no longer under way. End of `withPasskey`.

@@ 190-199
**Use a passkey instead** — on the sign-in form only, and only where the browser supports passkeys. No address or password to type.
