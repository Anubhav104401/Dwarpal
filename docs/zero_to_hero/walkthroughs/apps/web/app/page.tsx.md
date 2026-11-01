---
fingerprint: 7a3bdda4ceeac984
---
The **home page**, at `/` (§5.5.9): what Dwarpal is, for the people who take a check and for the websites that use one. It is the design's marketing site, apart from its 3D hero, which waits on decision D1. In Next.js's App Router, a file named `page.tsx` is the page for its folder's address: `app/page.tsx` is `/`.

@@ 53-73
**`Section`** — one titled section of the page: an `id` to link to (`scroll-mt-20` leaves room above it when a link scrolls there), a heading the section is named by (`aria-labelledby`, which also makes it a *region* for screen readers and tests), a lead paragraph, and its content.

@@ 75-78
**`Home`** — the page. It is an `async` server component: it asks the API for the model's figures while the page is made, on the server, so the figures arrive in the HTML itself, with no script. The demo shop's address comes from `DWARPAL_DEMO_SHOP_URL`; with none set (as when Dwarpal is hosted without the shop), the page doesn't offer a link that leads nowhere.

@@ 80-85
The page, and behind its top a soft saffron glow, as on the verify page: decoration, so hidden from screen readers.

@@ 86-102
The header: the mark and name; links to the sections, from the `lg` width up (on smaller screens the page simply scrolls), named by their words; the language switch (§5.5.11); and the console.

@@ 104-111
The hero: a badge that says plainly this is in development and decides test checks only; the motto as the page's one `h1`; and what Dwarpal does, in a sentence.

@@ 112-121
Two ways on: the demo shop, if the page knows where it is, and the developer section.

@@ 122-126
The hero (`_home/face-hero.tsx`), beside the words on a wide screen and below them on a phone: the doorway artwork, with its face in 3D where the browser can draw it.

@@ 128-140
**How it works**: an ordered list, since the steps happen in order, each in a panel.

@@ 142-153
**The privacy promise**, as a description list: each promise (`dt`) and what it means (`dd`).

@@ 155-157
**Accuracy, measured**: the live table (`_home/accuracy.tsx`), given what the API said.

@@ 159-172
**For developers**: the two pieces of code, each in a `figure` with a caption. `whitespace-pre-wrap` keeps the code's line breaks but lets a long line wrap, so the block never scrolls sideways — a box that scrolls must be reachable by keyboard, which the accessibility test enforces.

@@ 173-176
Where the full guides are: in the repository, for now; Dwarpal isn't hosted yet.

@@ 178-202
**Where it fits**: one panel per place, with the rule's name under it, then what it asks and how Dwarpal answers — side by side from the `md` width, stacked on a phone. (A table here needed sideways scrolling on a phone.)

@@ 203-204
The plain disclaimer: a draft summary, not yet reviewed by a lawyer (O5), and not legal advice.

@@ 206-225
**Questions**: each a `details` element, which the browser opens and closes by itself, with no script. `summary` is the part always shown; the `+` turns into an × (`group-open:rotate-45`) when its question is open.

@@ 227-242
The closing invitation: the demo shop, if known, and the console.

@@ 243-250
The end of the main part; the footer, and the end of the page.

@@ 1-4
Next.js's page-description type and its `Link` (moves between the app's own pages without reloading); next-intl's server translator (§5.5.11); and React's type for anything that can be drawn.

@@ 6-9
The language switch, the brand mark, the design system's badge, button classes and panel, and the reader for the model's published figures.

@@ 11-12
The page's own two pieces, in the private folder `_home`: a folder whose name starts with `_` never becomes an address. The accuracy table, and the hero (§5.5.10).

@@ 14-19
The page's title and description, for browser tabs and search results, in the visitor's language (`generateMetadata` runs per request, so it can ask for the request's words). The layout asks search engines to pass by every page; this one, the one meant to be found, overrides that (`index: true`).

@@ 21-22
Where to reach the API from the server: its internal address in production, else its public one, else this computer.

@@ 24-26
The page's words are in `messages/` (decision D2, §5.5.11), under `Home`; these lists are their **keys**, in the order shown:

- `STEPS` — **how it works**, the design's *Look. Decide. Forget.*: a live person in front of the camera, a decision that says yes only when sure (and *not sure* otherwise, so the website can offer a stronger check), and nothing kept;
- `PROMISES` — **the privacy promise**: four statements, each a property of how the system is built (§2, §5.1), which the practice statement makes too.

@@ 28-41
The quick-start's server code as text, shown on the page as it is in the developer guide (`docs/developers/README.md`): a client with the secret key and the API's address, and a function that creates a session and returns its link. Code isn't translated: it's the same in every language.

@@ 43-47
And the page's code: the React SDK's button, given that function (§5.5.7).

@@ 49-51
More keys:

- `LAWS` — **the compliance map** (UK, EU, US, Australia, India): for each, what the rule asks of an age check and how Dwarpal's design answers it, summarised from the problem analysis (`docs/design/01_problem_analysis.md` §3). Deliberately without fines or dates, which wait to be checked against primary sources;
- `QUESTIONS` — **the questions** people ask before looking at a camera, and honest answers — including that the model now running doesn't meet Dwarpal's own fairness standard;
- `SECTIONS` — the sections the header links to, by their `id` on the page.

@@ 79
The page's words, in the visitor's language.
