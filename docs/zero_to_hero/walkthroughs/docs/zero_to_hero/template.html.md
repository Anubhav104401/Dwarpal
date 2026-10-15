---
fingerprint: bf44bad5f9b94264
---
`template.html` is the **empty shell** of the book's page. It contains everything except the content: the page structure (HTML), all the styling (CSS, inside `<style>`) and the small amount of behaviour (JavaScript, inside `<script>`). Where content belongs it has **blanks** written as a word in double curly braces — `{{TITLE}}`, `{{TOC}}`, `{{BODY}}` and so on. `build.py` fills them in (see its lines 255–264).

The book must work as **one file, offline, with nothing downloaded from the internet**, so everything is *inline*: no external stylesheets, scripts or fonts.

**CSS in one minute.** A CSS *rule* looks like `selector { property: value; property: value; }`:

- the **selector** says *which* elements the rule applies to — `h1` means every `<h1>`, `.side` every element with `class="side"`, `#q` the element with `id="q"`;
- each **property: value** pair says *how* they should look.

When several rules apply to the same element, the more *specific* selector wins. Between equally specific rules, the one written later wins.

**JavaScript in one minute.** JavaScript is the browser's programming language. Here it does four small jobs:

1. remember and switch the colour theme;
2. filter the sidebar;
3. highlight the section you're reading;
4. draw the reading-progress bar.

@@ 1
`<!doctype html>` — the first line of every modern web page. It tells the browser "this is modern HTML; use standard rules". Without it, browsers fall back to an old compatibility mode ("quirks mode") that lays pages out differently.

@@ 2
`<html lang="en">` — the start of the page. Everything else sits inside it. `lang="en"` declares the language as English, which helps screen readers pronounce words correctly and helps browsers offer translation.

@@ 3
`<head>` — the page's "behind the scenes" section: settings, title and styles. Nothing in the head is shown directly in the page.

@@ 4
`<meta charset="utf-8">` — "this file's text is UTF-8". It must come early, before any text the browser might misread. Together with `build.py` writing UTF-8, this is what keeps `—`, `द्वारपाल` and 🧒 intact (§0.2).

@@ 5
`<meta name="viewport" …>` — makes phones show the page at its real width instead of pretending to be a wide desktop screen and shrinking everything. `initial-scale=1` means "start at 100 % zoom".

@@ 6
`<title>{{TITLE}}</title>` — the text shown on the browser tab. `{{TITLE}}` is a blank that `build.py` fills with the title from `book.toml`.

@@ 7
`<style>` — everything from here to `</style>` (line 138) is CSS.

@@ 8
`:root {` — `:root` selects the top element of the page (`<html>`). Rules here act as the page's **global settings**. The `{` opens the list of settings.

@@ 9
`color-scheme: light dark;` — tells the browser this page supports both light and dark modes. The browser then picks one based on the user's system setting. This also switches built-in parts (scrollbars, the search box) to matching colours.

@@ 10-21
**The colour palette, defined once.** Names starting with two dashes (`--bg`, `--text`, …) are **CSS custom properties**, also called *CSS variables*: named values that other rules reuse as `var(--bg)`. Changing a colour here changes it everywhere.

Each colour uses **`light-dark(A, B)`**: "use A in light mode and B in dark mode". One line per colour covers both themes. The names describe *roles*, not colours:

| Variable | Role |
| :-- | :-- |
| `--bg`, `--bg-2`, `--bg-3` | page background, panels, slightly darker panels |
| `--text`, `--text-2`, `--text-3` | main text, secondary text, faint text |
| `--border` | lines and box edges |
| `--accent` | links and highlights (blue) |
| `--ok`, `--warn`, `--danger`, `--purple` | green, amber and red status colours, and purple for the "kid" boxes |

The colour values are written in **hexadecimal**: `#` then two digits each for red, green and blue (`00`–`ff`, i.e. 0–255). `#ffffff` is white; `#0d1117` is a very dark blue-grey. These are GitHub's own interface colours, chosen to match the earlier AegisProxy book the project owner liked, and because they are tuned for readability.

!!! why "Why `light-dark()` instead of writing two separate colour lists?"
    The older approach repeats the whole dark palette twice: once for "the system is in dark mode" and once for "the user clicked the dark button". Two copies inevitably drift apart. `light-dark()` (supported by all major browsers since 2024) needs each colour exactly once.

@@ 22
`--sans` — the font for normal text: a **font stack**, a list of fonts in order of preference. `system-ui` means "the operating system's own interface font" (Segoe UI on Windows, San Francisco on Apple devices). If one font is missing, the browser tries the next. Using fonts already on the device means nothing has to be downloaded.

@@ 23
`--mono` — the font stack for code: **monospaced** fonts, where every character is the same width so code lines up. Cascadia Code ships with Windows Terminal; the others cover macOS and Linux.

@@ 24
`}` — closes the `:root` rule.

@@ 25-26
**The theme buttons' effect.** When JavaScript sets `data-theme="light"` or `"dark"` on the page, these rules *force* that colour scheme. Every `light-dark()` above then follows it, regardless of the system setting. `[data-theme="light"]` is an **attribute selector**: it matches elements whose `data-theme` attribute has that value.

@@ 27
`*, *::before, *::after { box-sizing: border-box; }` — `*` means "every element", and `::before`/`::after` are the invisible extra boxes CSS can attach to elements.

By default, an element's *width* doesn't include its padding and border, so a "300-pixel" box with padding ends up wider than 300 pixels — a classic source of layout confusion. `border-box` makes width mean *total* width. Almost every modern site starts with this line.

@@ 28
`body { … }` — the visible page:

- `margin: 0` removes the browser's default gap around the page;
- the background and text colours come from the palette;
- `font: 16px/1.7 var(--sans)` is shorthand for "16-pixel text, line spacing 1.7 times the text size, in the sans font".

The generous 1.7 line spacing makes long explanations easier to read.

@@ 30
`/* … */` is a **CSS comment** — a note for humans that the browser ignores. Comments like this one divide the stylesheet into labelled sections.

@@ 31
`.shell` — the two-column frame of the page. `display: grid` turns it into a **grid**; `grid-template-columns` defines two columns:

- `300px` for the sidebar;
- `minmax(0, 1fr)` for the reading area. `fr` means "a fraction of the remaining space". The `minmax(0, …)` lets the column shrink below its content's natural width, so a wide code block scrolls *inside* its box instead of stretching the whole page sideways.

`min-height: 100vh` makes it at least as tall as the window. `vh` is a percentage of the *viewport height*.

@@ 32-33
`.side` — the sidebar:

- `position: sticky; top: 0` makes it stay pinned to the top of the window while the page scrolls;
- `height: 100vh` with `overflow-y: auto` gives it its own scrollbar when the table of contents is taller than the window;
- it has a panel-coloured background, a thin right border separating it from the content, and padding (inner space: 18 px at the top, 0 at the sides, 40 px at the bottom).

@@ 34
`.side-head` — the sidebar's top block (title and statistics): padding around it and a dividing line underneath.

@@ 35
`.side-head .name` — the book title in the sidebar. A space between two selectors means "inside": an element with class `name` *inside* `.side-head`. `font-weight: 700` is bold.

@@ 36
`.side-head .meta` — the small statistics line (word count, coverage): small monospaced text in the faint colour, with a little space above it.

@@ 37-38
`#q` — the sidebar's filter box (its `id` is `q`, for *query*). `calc(100% - 36px)` computes "full width minus 36 pixels", leaving room for the 18-pixel margins on each side. It has rounded corners (`border-radius`) and theme colours, so the box matches light and dark modes.

@@ 39-40
`.toc a` — the sidebar's links (`a` is the HTML *anchor*, i.e. link, element):

- `display: block` makes each link a full-width line, so the whole line is clickable;
- `text-decoration: none` removes underlines;
- the transparent left border reserves space for the blue bar that marks the active section (line 45), so nothing shifts when it appears.

@@ 41
`.toc a:hover` — `:hover` is a **pseudo-class** meaning "while the mouse is over it". Hovered links get darker text and a light background.

@@ 42-44
**Indenting by heading level.** `build.py` gives each link a class named after its heading's level:

- `h1` — parts: bold, with space above, so each part starts a visible group;
- `h2` — sections: indented 30 px;
- `h3` — sub-sections: indented 44 px, smaller and fainter.

@@ 45
`.toc a.active` — the link for the section you're currently reading: blue text, a blue left bar and a light background. JavaScript adds and removes the `active` class (lines 183–184).

@@ 46
`.toc a[hidden] { display: none; }` — hides links that the filter has marked `hidden`.

!!! real "Real world — a bug caught before it shipped"
    HTML's `hidden` attribute normally hides an element by itself. But line 39 says `display: block` for every sidebar link, and a page's own CSS beats the browser's built-in rules. So without this line, "hidden" links would stay visible and the filter would do nothing. This line restores hiding with a more specific selector. Mistakes like this are why every line deserves a careful look.

@@ 47
`main` — the reading column:

- generous padding on each side (48 px top, 56 px sides, 160 px bottom, so the last line isn't stuck to the window edge);
- `max-width: 1180px`, because lines of text longer than that are tiring to read;
- `min-width: 0`, the same anti-stretching trick as on line 31.

@@ 48
`.topbar` — the box holding the **Top** and **Theme** buttons. `position: fixed` pins it to the window itself — 14 px from the top, 18 px from the right — however far you scroll.

- `display: flex` lines its children up in a row;
- `gap` puts 8 px between them;
- `z-index: 20` stacks it *above* the page content, so text scrolls *under* the buttons rather than over them.

@@ 49-50
`.topbar button` — the buttons' look: a thin border, panel background, rounded corners, small text. `cursor: pointer` shows the hand-shaped pointer, signalling "clickable".

@@ 51
On hover, the button's text darkens — a small sign that it reacts.

@@ 52-53
`#progress` — the thin blue **reading-progress bar** at the very top of the window.

- `inset: 0 0 auto 0` pins its top, right and left edges to the window and leaves the bottom free, so it's a full-width strip 3 px tall.
- `transform: scaleX(0)` shrinks it horizontally to nothing at first. JavaScript stretches it as you scroll (line 193).
- `transform-origin: left` makes it grow from the left edge.
- `z-index: 30` keeps it above everything, including the buttons.

@@ 55
Section comment: the rules that shape text.

@@ 56
**All headings, levels 1–4:**

- tight line spacing (1.3);
- space above (2em — *em* means "times the current text size") and below (0.6em);
- letters pulled very slightly closer (`letter-spacing`), which looks better at large sizes.

`scroll-margin-top: 24px` leaves a little space above a heading when you jump to it from the sidebar, so it doesn't sit flush against the window edge.

@@ 57-58
**Part titles (`h1`) and section titles (`h2`)**: progressively smaller sizes, each with a thin underline drawn by `border-bottom`, like GitHub's documentation style.

@@ 59-60
**Smaller headings**: `h3` slightly larger than body text; `h4` about body size, in the secondary colour.

@@ 61
`main > h1:first-child` — the very first heading of the page. `>` means "directly inside", and `:first-child` means "the first element in its parent". This removes its top margin, so the book doesn't start with an awkward gap.

@@ 62
Paragraphs, lists and definition lists get no space above and 1em below — consistent rhythm between blocks.

@@ 63
Lists are indented 1.6em, which leaves room for bullets and numbers.

@@ 64
A little breathing room between list items.

@@ 65-66
**Links:** accent colour, no underline — except while hovered, so it's clear they're clickable.

@@ 67
`hr` — the horizontal divider line, restyled as a single thin border line with generous space around it.

@@ 68
`blockquote` — quoted text: a thick grey bar on the left and the secondary text colour.

@@ 69
`abbr[title]` — words with hover definitions (from `abbreviations.md`): a dotted underline, and `cursor: help` (a question-mark pointer) hinting "hover me for an explanation".

@@ 70-71
**Definition lists** (used by the Glossary): the term (`dt`) in bold; its definition (`dd`) indented, with space below.

@@ 73
Section comment: code styling.

@@ 74-75
`code` — short code inside a sentence, like `build.py`: monospaced, slightly smaller, on a tinted background with rounded corners, so it stands out from prose.

The second line, `font-variant-ligatures: none`, switches off **ligatures**. Some coding fonts, including Cascadia Code, merge certain character pairs into one symbol: `->` is drawn as a single arrow `→`, and `!=` as `≠`. Experienced programmers like this, but a beginner reading `→` would hunt for an arrow key that doesn't exist. In this book, code must look exactly like what you would type.

`code` also applies inside code blocks (the `pre code` rule below only changes the background, padding and size), so this one setting covers every piece of code in the book.

@@ 76-77
`pre` — blocks of code. `pre` means *pre-formatted*: spaces and line breaks are kept exactly as written, which code needs.

- Panel background, border, rounded corners and padding.
- `overflow-x: auto` adds a sideways scrollbar for long lines instead of wrapping them; wrapped code is confusing.
- Slightly taller line spacing and a 13 px font.

@@ 78
`pre code` — code *inside* a code block shouldn't also get the inline-code background and padding from line 74, so this removes them. `font-size: inherit` takes the block's size instead of shrinking again.

@@ 79-85
**Syntax-highlighting colours.** Pygments labels each piece of code with a short class name, and these rules colour the classes. Each uses `light-dark()` for both themes, with GitHub's code colours:

| Classes | Pygments meaning | Colour |
| :-- | :-- | :-- |
| `k kn kd kr kc ow o` | keywords (`def`, `import`, `return`, `True`), word operators (`and`, `not`), operators | red |
| `s s1 s2 sd sa sb sh dl` | strings of all kinds, and their quote marks | dark blue / light blue |
| `c c1 cm ch cs cp` | comments of all kinds | grey italic |
| `nf fm nd` | function names, special `__methods__`, decorators | purple |
| `nc nn` | class names, module names | orange-brown |
| `nb bp kt na se si sr m mi mf mh` | built-ins (`len`, `self`), types, attributes, escapes, numbers | blue |
| `nt` | HTML tag names | green |

Each selector starts with `.hl ` (with a space), so only code inside highlighted boxes is coloured.

@@ 87
Section comment: tables.

@@ 88
`.tw` — the wrapper `build.py` puts around every table (its line 240). On narrow screens it scrolls sideways, and it gives the table a rounded border.

@@ 89
`table` — full width, with `border-collapse: collapse` so neighbouring cells share one border line instead of drawing two.

@@ 90
`th, td` — header cells and data cells: padding, a line underneath, text aligned left and to the top. Top alignment matters when one cell has more lines than its neighbours.

@@ 91
Header cells get a panel background and semi-bold text.

@@ 92
The last row has no bottom line, because the wrapper's own border is already there. Without this, the bottom edge would look doubled.

@@ 94
Section comment: the coloured callout boxes, written `!!! kid "Title"` in chapters.

@@ 95-96
`.admonition` — the shared look of every box. It sets two **local variables** with defaults:

- `--c` — the box's colour (default: faint grey);
- `--icon` — its emoji (default: ℹ️).

The box has a thick left border in `--c`, rounded right corners, and a background made by `color-mix(in srgb, var(--c) 9%, transparent)` — "9 % of the box colour, the rest see-through". That gives a soft tint matching the border in both themes, with no extra colour definitions.

@@ 97
Removes the bottom margin of the box's last element, so the space inside is even at top and bottom.

@@ 98
`.admonition-title` — the box's title line: bold, with a little space below.

@@ 99
`.admonition-title::before` — a **pseudo-element**: content CSS inserts *before* the title text. `content: var(--icon) "  "` inserts the box's emoji followed by two spaces. The icon therefore comes from CSS, so chapter authors never type it.

@@ 100-108
**One line per box type**, each setting only its colour and icon:

| Box | Colour | Icon |
| :-- | :-- | :-- |
| `kid` | purple | 🧒 |
| `key` | blue | 🔑 |
| `why` | green | 🤔 |
| `alt` | grey | 🔀 |
| `warn` | amber | ⚠️ |
| `try` | green | 🧪 |
| `word` | blue | 📖 |
| `real` | amber | 🌍 |
| `honest` | red | 🙋 |

Because the shared look lives on lines 95–99, adding a new kind of box takes a single line.

@@ 110
Section comment: the line-by-line walkthroughs — the part you are looking at right now.

@@ 111
`.walk` — the frame around one file's walkthrough: a border with rounded corners, and space below. `overflow: hidden` clips the inner rows to the rounded corners, so square corners don't poke out.

@@ 112-113
`.whead` — the header bar showing the file path, line count and coverage. `display: flex` lines the pieces up in a row, `flex-wrap: wrap` lets them flow onto a second line on narrow screens, and `gap` spaces them.

@@ 114
`.whead code` — the file path in the header bar: no inline-code background (the whole bar is already tinted), bold, in the main text colour.

@@ 115
`.wintro` — the file's introduction, with padding to line it up with the rows below.

@@ 116
`.wrow` — one row: code on the left, explanation on the right. It's a two-column grid in an 11 : 9 ratio, so the code gets slightly more room. `minmax(0, …)` again stops long lines from stretching the layout. Each row has a line above it.

@@ 117
Inside a row, the code box loses its own margin, border and rounded corners — the row and frame provide those — and gets slightly tighter padding.

@@ 118
`.wnote` — the explanation side: padding, and text a little smaller than the main text so dense explanations stay compact.

@@ 119
Removes the bottom margin of the last element in each explanation, so short notes don't end with a gap.

@@ 120
`.wrow.blank pre` — rows containing only blank lines get no vertical padding. Two class names written together with no space (`.wrow.blank`) mean "an element that has **both** classes".

@@ 121
`.wrow.blank .wnote { display: none; }` — rows that contain only blank lines have nothing to explain, so their (empty) explanation box is removed entirely. Without this, the narrow one-column layout showed an empty box with a dashed line under every blank line — visual noise that made the real explanations harder to follow.

@@ 122
`.wrow.missing` — rows with **unexplained** code get a red bar down their left edge. `box-shadow: inset 4px 0 var(--danger)` draws a "shadow" 4 px wide *inside* the left edge, without changing the row's size.

@@ 123
`.ln` — the line numbers next to the code:

- `inline-block` with a minimum width of three characters, right-aligned, so numbers line up whether they have one digit or three;
- faint colour, so they don't compete with the code;
- `user-select: none` stops them being copied when you select and copy code from the page.

@@ 124
`.todo` — the red, bold "Not explained yet." message.

@@ 125
`.pill` — the small rounded labels ("complete", "stale"…). `border-radius: 99px` is larger than any pill's height, which makes the ends perfectly round. `white-space: nowrap` stops a two-word label such as "not explained" from breaking across two lines.

@@ 126-128
The pill colours: green for good, amber for in progress, red for problems. Each has a soft tinted background made with `color-mix`, as on line 96.

@@ 129
`footer` — the small grey line at the very end showing when the book was built.

@@ 131
**`@media (max-width: 1100px)`** — a **media query**: rules that apply only when the condition is true, here "the window is 1100 px wide or less". On such screens, walkthrough rows switch to one column (code above, explanation below), with a dashed line between them. Side-by-side columns would be too narrow to read.

@@ 132-136
**On screens 900 px wide or less** (tablets and phones):

- the page becomes a single column;
- the sidebar stops being sticky, takes its natural height, and sits above the content with a line below it instead of beside it;
- the side padding shrinks to 16 px, so text uses the small screen fully.

@@ 137
**When printing** (`@media print`), the sidebar, buttons and progress bar are hidden and the grid is switched off, so paper gets just the content.

@@ 138
`</style>` — the end of the CSS.

@@ 139
`</head>` — the end of the behind-the-scenes section.

@@ 140
`<body>` — the start of everything visible.

@@ 141
`<div id="progress"></div>` — the empty element that becomes the progress bar. A `div` is a general-purpose box with no meaning of its own; its look comes entirely from CSS (lines 52–53).

@@ 142
**The two buttons.** `type="button"` says plainly that they don't submit any form. Each has an `id` so JavaScript can find it.

@@ 143
`<div class="shell">` — the two-column grid from line 31.

@@ 144
`<aside class="side">` — the sidebar. `<aside>` is a *semantic* element: it tells browsers and screen readers "this is supporting content beside the main content", which a plain `div` would not.

@@ 145
The sidebar header. `{{TITLE}}` and `{{META}}` are filled by `build.py` with the title and the "words · files · coverage" statistics.

@@ 146
**The filter box:**

- `type="search"` gives a search field (on many browsers, with a clear button);
- `placeholder` is the grey hint text shown while it's empty;
- `autocomplete="off"` stops the browser from suggesting old entries;
- `aria-label` gives screen readers a name for the box, because it has no visible label. *ARIA* is a set of attributes that make pages accessible to people using assistive technology.

@@ 147
`<nav class="toc">{{TOC}}</nav>` — the table of contents. `<nav>` marks a navigation block for assistive technology. `{{TOC}}` becomes the list of links.

@@ 148
`</aside>` — the sidebar ends.

@@ 149
`<main>` — the main content. A page should have exactly one `<main>`; screen readers offer a shortcut to jump straight to it.

@@ 150
`{{BODY}}` — **the entire book** goes here: every chapter, walkthrough and table. It sits alone on its line at the far left so the inserted HTML isn't shifted by indentation. `build.py` fills it last, deliberately (see its line 264).

@@ 151
The footer, filled with the subtitle and the build time.

@@ 152-153
Close `<main>`, then the shell grid.

@@ 154
`<script>` — everything from here to `</script>` is JavaScript. It sits at the very end of the page, so when it runs, all the elements it looks for already exist.

@@ 155
`(() => {` — the start of an **immediately invoked function**. `() => { … }` defines a small unnamed function (an *arrow function*); wrapping it in parentheses and adding `()` at the end (line 197) runs it straight away. Every name created inside stays private to it and can't clash with anything else on the page.

@@ 156
`const root = document.documentElement;` — `const` creates a name that won't be reassigned. `document` is the browser's object representing the whole page, and `documentElement` is its top element, `<html>` — the same element CSS calls `:root`.

@@ 157
`remember` — a tiny function that saves the chosen theme in **localStorage**, the browser's small per-site storage that survives closing the tab. It is wrapped in `try { … } catch {}` because storage can be unavailable — some private-browsing modes, or files opened in restricted viewers throw an error — and a failure to *remember* must never break the button itself.

@@ 158
**On page load, restore the saved theme.** Read `"z2h-theme"` from storage. If something was saved, set the page's `data-theme` attribute to it. `root.dataset.theme` is JavaScript's way of reading and writing a `data-theme` attribute. Again it is wrapped in `try`, for the same reason.

@@ 159
**When the Theme button is clicked…** `document.getElementById("theme")` finds the button by its `id`. `addEventListener("click", …)` says "whenever it is clicked, run this function".

@@ 160
**…work out whether the page is dark right now.** If a theme was chosen explicitly, it's dark if that choice is `"dark"`. Otherwise, ask the system: `matchMedia("(prefers-color-scheme: dark)").matches` is `true` when the operating system is in dark mode. The `? :` is JavaScript's conditional expression: *condition* `?` *if true* `:` *if false*.

@@ 161
**…switch to the opposite.** Setting `data-theme` triggers the CSS on lines 25–26, and every colour flips instantly.

@@ 162
**…and remember the choice** for next time.

@@ 163
`});` — closes the click handler, then the `addEventListener` call.

@@ 164
**The Top button:** when clicked, scroll the window to the top. `behavior: "smooth"` glides there instead of jumping.

@@ 166
`filter` — the search box, found by its `id`.

@@ 167
`links` — every link in the table of contents. `querySelectorAll(".toc a")` finds all elements matching a CSS selector. `[... ]` with three dots copies the results into a real **array** (JavaScript's list), which has more handy methods.

@@ 168
**Every time the filter's text changes** (each typed or deleted character fires an `"input"` event)…

@@ 169
…take the typed text, lower-cased and trimmed of spaces, so matching ignores capital letters.

@@ 170
…and for each link, set `hidden` to `true` if something was typed **and** the link's text doesn't contain it. An empty box therefore shows every link. `!==` means "is not equal to"; `!` means "not".

@@ 171
Closes the input handler.

@@ 172
**Keyboard shortcuts:** listen to every key pressed anywhere on the page. `event` describes the key press.

@@ 173
**Ctrl + K** (or **Cmd + K** on a Mac, the "meta" key) jumps to the filter box. `preventDefault()` stops the browser's own Ctrl + K action (in some browsers, focusing the address bar). `focus()` puts the cursor in the box, and `select()` highlights any old text so typing replaces it.

@@ 174
**Escape** while typing in the filter: clear it, announce the change (`dispatchEvent(new Event("input"))` makes the line-168 handler run, so all links reappear), and leave the box (`blur`).

@@ 175
Closes the keyboard handler.

@@ 177
`side` — the sidebar element, needed to scroll it on line 185.

@@ 178
`byId` — a **Map** (a dictionary) from a heading's `id` to its sidebar link. `link.hash` is the `#part-0-absolute-basics` part of the link's address; `.slice(1)` drops the `#`. `decodeURIComponent` turns any encoded characters (`%20` and similar) back into normal text, so the key matches the heading's real `id`.

@@ 179
**The "section spy".** An **IntersectionObserver** is a browser feature that tells you when watched elements enter or leave the visible area. It's far cheaper than checking positions on every scroll. The function given to it runs with a list of `entries`, one per watched heading that changed.

@@ 180
For each change…

@@ 181
…if the heading has just become visible, look up its sidebar link. `a && b` gives `b` only if `a` is true; otherwise it gives `false`.

@@ 182
If there's no link — the heading went out of view, or isn't listed in the sidebar — skip to the next entry.

@@ 183
Remove the `active` class from every link…

@@ 184
…and add it to this one. The blue highlight from CSS line 45 moves to the section you're reading.

@@ 185
**Keep the active link in view.** If the sidebar has its own scrollbar (its content is taller than its visible height), scroll it so the active link sits about a third of the way down. On phones the sidebar isn't scrollable, so nothing moves — which also stops the page from jumping back to the top.

@@ 186
Closes the loop.

@@ 187
**Observer options.** `rootMargin: "0px 0px -75% 0px"` shrinks the "visible area" to the **top quarter** of the window, so a heading counts as "current" once it reaches the upper part of the screen. That matches where your eyes are when you start a new section.

@@ 188
**Start watching** every `h1`, `h2` and `h3` inside `<main>` that has an `id`. `:is(h1, h2, h3)` is CSS shorthand for "any of these".

@@ 190
`bar` — the progress-bar element.

@@ 191
`onScroll` — a function, stored in a constant, that updates the bar.

@@ 192
`max` — how far the page *can* scroll: the full height of the page (`scrollHeight`) minus the height of the window (`innerHeight`).

@@ 193
**Stretch the bar.** `scrollY / max` is the fraction scrolled so far, from 0 at the top to 1 at the bottom; `scaleX` stretches the bar by that fraction. The text in back-ticks is a **template literal**: `${…}` inside it inserts a value, like Python's f-strings. The `max > 0 ?` check avoids dividing by zero on a page too short to scroll.

@@ 194
Closes the `onScroll` function.

@@ 195
**Run `onScroll` whenever the page scrolls.** `{ passive: true }` promises the browser that this function will never cancel the scroll, so the browser can scroll smoothly without waiting for it.

@@ 196
Run it once straight away, so the bar is right even before the first scroll — for example when the page is reloaded halfway down.

@@ 197
`})();` — closes the immediately invoked function from line 153 and runs it.

@@ 198
`</script>` — the end of the JavaScript.

@@ 199-200
`</body>` and `</html>` — the end of the visible content, and the end of the page.
