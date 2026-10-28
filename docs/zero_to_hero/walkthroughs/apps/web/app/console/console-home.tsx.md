---
fingerprint: ac4762fc9a1deb2e
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

@@ 82-99
**Signed in**: the frame shows the person's address (on wider screens), a link to the *Age model* page (§5.5.2), a link to their *Security* page (§5.5.4), and a *Sign out* button.

@@ 100
The heading.

@@ 101-113
Each organisation as a card linking to its page, with the person's role in it. Its border turns saffron on hover, with a short transition — only for people who haven't asked for reduced motion (`motion-safe:`).

@@ 114-116
End of the signed-in view.

@@ 118
**Nobody signed in**: which mode is the form in?

@@ 119-124
The frame, a card, and the heading for the mode.

@@ 125-127
A sentence that says who the console is for — and that people whose age is checked never need an account.

@@ 128
The form.

@@ 129-131
The e-mail field. `autoComplete="email"` lets the browser or a password manager fill it in.

@@ 132-142
The password. The `autoComplete` hint tells password managers whether to suggest a new one (signing up) or fill the saved one (signing in); signing up asks for 12 characters before the API would.

@@ 143-153
When signing up, the organisation's name.

@@ 154-169
When the API has asked for it, the code: `autoComplete="one-time-code"` lets phones offer a code they have just received; the pattern accepts six digits or a recovery code, and a hint underneath — tied to the field with `aria-describedby`, so screen readers read it too — says a recovery code works when the phone is lost.

@@ 170
The error, if there is one, announced to screen readers (`Alert`).

@@ 171-173
The submit button, disabled while a request is under way so it can't be sent twice.

@@ 174
End of the form.

@@ 175-184
A button that switches between signing in and creating an account, clearing any error from the other mode.

@@ 185-188
End of the card, the frame and the component.
