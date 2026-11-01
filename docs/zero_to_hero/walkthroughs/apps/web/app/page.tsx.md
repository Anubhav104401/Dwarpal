---
fingerprint: ca415e209fec4a85
---
The **home page**, at `/` (§5.5.9): what Dwarpal is, for the people who take a check and for the websites that use one. It is the design's marketing site, apart from its 3D hero, which waits on decision D1. In Next.js's App Router, a file named `page.tsx` is the page for its folder's address: `app/page.tsx` is `/`.

@@ 1-3
Next.js's page-description type and its `Link` (moves between the app's own pages without reloading); React's type for "anything that can be shown".

@@ 5-7
Dwarpal's mark, from the verify page's frame; the button classes, the badge and the raised panel, from the design system (§5.5.6); and the function that asks the API for the model's figures.

@@ 9-10
The page's own two pieces, in the private folder `_home`: a folder whose name starts with `_` never becomes an address.

@@ 12-18
The page's title and description, for browser tabs and search results. The layout asks search engines not to index any page (the console and the verify page are private); this page overrides that with `index: true`, since it is the one that should be found. The Lighthouse test holds its search score to 90.

@@ 20-21
Where this server reaches the API: the private address if one is set, otherwise the public one, otherwise the developer's computer — the same order as `proxy.ts`.

@@ 23-36
**How it works**, in three steps, the design's *Look. Decide. Forget.*: a live person in front of the camera, a decision that says yes only when sure (and *not sure* otherwise, so the website can offer a stronger check), and nothing kept but a signed answer.

@@ 38-49
**The privacy promise**: four statements, each a property of how the system is built (§2, §5.1), which the practice statement makes too.

@@ 51-64
The quick-start's server code as text, shown on the page as it is in the developer guide (`docs/developers/README.md`): a client with the secret key and the API's address, and a function that creates a session and returns its link. The backticks make a JavaScript **template string**, which can run over several lines.

@@ 66-70
And the page's code: the React SDK's button, given that function (§5.5.7).

@@ 72-103
**The compliance map** (UK, EU, US, Australia, India): for each, what the rule asks of an age check and how Dwarpal's design answers it, summarised from the problem analysis (`docs/design/01_problem_analysis.md` §3). Deliberately without fines, dates or figures: those are to be checked against primary sources before anything compliance-facing states them, and the page says it is a summary, not legal advice.

@@ 105-130
**The questions** people ask before looking at a camera, and honest answers — including that the model now running doesn't meet Dwarpal's own fairness standard, and that ID-document checks aren't built yet.

@@ 132-138
The sections the header links to: each pair is an `id` on the page and the link's text.

@@ 140-160
**`Section`** — one titled section of the page: an `id` to link to (`scroll-mt-20` leaves room above it when a link scrolls there), a heading the section is named by (`aria-labelledby`, which also makes it a *region* for screen readers and tests), a lead paragraph, and its content.

@@ 162-165
**`Home`** — the page. It is an `async` server component: it asks the API for the model's figures while the page is made, on the server, so the figures arrive in the HTML itself, with no script. The demo shop's address comes from `DWARPAL_DEMO_SHOP_URL`; with none set (as when Dwarpal is hosted without the shop), the page doesn't offer a link that leads nowhere.

@@ 166-171
The page, and behind its top a soft saffron glow, as on the verify page: decoration, so hidden from screen readers.

@@ 172-185
The header: the mark and name; links to the sections, from the `md` width up (on a phone, the page simply scrolls); and the console's sign-in.

@@ 187-195
The hero: a badge that says plainly this is in development and decides test checks only; the motto as the page's one `h1`; and what Dwarpal does, in a sentence.

@@ 196-205
Two ways on: the demo shop, if the page knows where it is, and the developer section.

@@ 206-210
The artwork (`_home/arch.tsx`), beside the words on a wide screen and below them on a phone.

@@ 212-226
**How it works**: an ordered list, since the steps happen in order, each in a panel.

@@ 228-241
**The privacy promise**, as a description list: each promise (`dt`) and what it means (`dd`).

@@ 243-249
**Accuracy, measured**: the live table (`_home/accuracy.tsx`), given what the API said.

@@ 251-268
**For developers**: the two pieces of code, each in a `figure` with a caption. `whitespace-pre-wrap` keeps the code's line breaks but lets a long line wrap, so the block never scrolls sideways — a box that scrolls must be reachable by keyboard, which the accessibility test enforces.

@@ 269-274
Where the full guides are: in the repository, for now; Dwarpal isn't hosted yet.

@@ 276-300
**Where it fits**: one panel per place, with the rule's name under it, then what it asks and how Dwarpal answers — side by side from the `md` width, stacked on a phone. (A table here needed sideways scrolling on a phone.)

@@ 301-305
The plain disclaimer: a draft summary, not yet reviewed by a lawyer (O5), and not legal advice.

@@ 307-324
**Questions**: each a `details` element, which the browser opens and closes by itself, with no script. `summary` is the part always shown; the `+` turns into an × (`group-open:rotate-45`) when its question is open.

@@ 326-343
The closing invitation: the demo shop, if known, and the console.

@@ 344-351
The end of the main part; the footer, and the end of the page.
