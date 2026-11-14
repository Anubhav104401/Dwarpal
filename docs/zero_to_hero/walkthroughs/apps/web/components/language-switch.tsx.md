---
fingerprint: b7e47bae551e3571
---
The **language menu** (§5.5.11, and since 14 Nov §7.15): ten languages, on the home page's header and under the verify page. Until 14 Nov it was two buttons side by side, English and हिन्दी; ten buttons don't fit a phone's header, so it became a small menu that opens. It is still plain HTML — a `<details>` element and a form — so it works without JavaScript too.

@@ 1-6
next-intl's current language and translator; the server action and the languages; and the button classes.

@@ 8-12
The component's comment: what the menu shows, and why it needs no script. **`<details>`** is an HTML element that hides its contents until its first child, the **`<summary>`**, is clicked — the browser opens and closes it by itself, the way the home page's questions open.

@@ 13-15
**`LanguageSwitch`** — it needs the page's current language and its own words (`Language` in `messages/`).

@@ 16-18
The `<details>`, keyed by the current language. React reuses an element whose **key** hasn't changed, and that kept the menu open after a choice: the page came back in the new language with the list still showing. A new key makes React build a fresh, closed one. `group` and `relative` let the arrow below turn when it's open, and the list float under it.

@@ 19-22
The **summary** — the part that's always visible — styled as a quiet button. `list-none` and the `::-webkit-details-marker` rule hide the triangle browsers draw by themselves. Its `aria-label` tells screen readers what it is and what is chosen: "Language: English", or "भाषा: हिन्दी".

@@ 23-27
What it shows: the current language's own name (`lang` so screen readers pronounce it right), and a small arrow, hidden from screen readers, that turns over (`group-open:rotate-180`) while the menu is open.

@@ 28-32
The list: a **form** whose action is the server action (`chooseLocale`), named for screen readers, floating under the summary (`absolute right-0`) above the page (`z-20`), as a white card — dark in the dark theme.

@@ 33-45
One submit button per language: pressing it sends `locale=ta` (say) with the form, and the page comes back in Tamil. `lang` tells screen readers how to pronounce each name, and `aria-pressed` says which language is on now; the pressed one gets a soft background in both themes. Its text is the language's own name.

@@ 46-49
The end of the list, the form, the menu and the component.
