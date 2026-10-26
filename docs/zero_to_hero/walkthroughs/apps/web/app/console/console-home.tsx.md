---
fingerprint: 1dcc9109e23b85f2
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
The client, its error, and the `Me` type.

@@ 17
One client for the page. It keeps the CSRF token, so it must live as long as the page does.

@@ 19
The form's two modes.

@@ 21-22
**`explain`** — plain words for the refusals a person can do something about.

@@ 23
Anything that isn't a refusal from the API (the network failed, say) gets a general sentence.

@@ 24-32
The refusals by their stable code, each with a sentence that says what to do.

@@ 33
A code without its own sentence shows the API's own detail.

@@ 34
End of `explain`.

@@ 36-41
**`ConsoleHome`**, and what it remembers: who is signed in (`undefined` while unknown, `null` for nobody), the form's mode, whether the code field is needed, the current error, and whether a request is under way.

@@ 43-45
Once, when the page first appears, ask the API who is signed in. If that fails at all, treat it as nobody.

@@ 47-50
**`submit`** — the form was sent. `preventDefault` stops the browser's own submission (which would reload the page); `FormData` reads the fields by name.

@@ 51-52
Mark the request as under way (the button greys out), and clear the old error.

@@ 53-58
Sign in or sign up, and remember who that makes signed in. An empty code is sent as no code.

@@ 59-61
On a refusal, show the code field if the API asked for one, and show the explanation.

@@ 62-64
In every case, the request is no longer under way.

@@ 65
End of `submit`.

@@ 67-70
**`signOut`** — end the session and show the sign-in form again.

@@ 72-80
Still asking: show *Loading…* in a region screen readers announce politely.

@@ 82-93
**Signed in**: the frame shows the person's address (on wider screens) and a *Sign out* button.

@@ 94
The heading.

@@ 95-107
Each organisation as a card linking to its page, with the person's role in it.

@@ 108-110
End of the signed-in view.

@@ 112
**Nobody signed in**: which mode is the form in?

@@ 113-118
The frame, a card, and the heading for the mode.

@@ 119-121
A sentence that says who the console is for — and that people whose age is checked never need an account.

@@ 122
The form.

@@ 123-125
The e-mail field. `autoComplete="email"` lets the browser or a password manager fill it in.

@@ 126-136
The password. The `autoComplete` hint tells password managers whether to suggest a new one (signing up) or fill the saved one (signing in); signing up asks for 12 characters before the API would.

@@ 137-147
When signing up, the organisation's name.

@@ 148-160
When the API has asked for it, the one-time code: a number pad on phones (`inputMode="numeric"`), exactly six digits, and `autoComplete="one-time-code"`, which lets phones offer a code they have just received.

@@ 161
The error, if there is one, announced to screen readers (`Alert`).

@@ 162-164
The submit button, disabled while a request is under way so it can't be sent twice.

@@ 165
End of the form.

@@ 166-175
A button that switches between signing in and creating an account, clearing any error from the other mode.

@@ 176-179
End of the card, the frame and the component.
