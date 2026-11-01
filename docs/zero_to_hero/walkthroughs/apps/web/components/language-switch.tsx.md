---
fingerprint: 6f7fc62e70229dda
---
The **language switch** (§5.5.11): English or हिन्दी, on the home page's header and under the verify page. It is a plain form, so it works without JavaScript too.

@@ 1-6
next-intl's current language and translator; the server action and the languages; and the button classes.

@@ 8-11
**`LanguageSwitch`** — its comment: each language's name is written in its own language and script — "English", "हिन्दी" — so a person who reads only one of them can still find theirs. It needs the page's current language and its own words (`Language` in `messages/`).

@@ 12-13
A **form** whose action is the server action, named for screen readers ("Language", or "भाषा").

@@ 14-21
One submit button per language: pressing it sends `locale=hi` (say) with the form. `lang` tells screen readers how to pronounce each name, and `aria-pressed` says which language is on now.

@@ 22-25
Quiet, compact buttons; the pressed one (`aria-pressed:` styles) gets a soft background, in both themes. Its text is the language's own name.

@@ 26-29
The end of the list, the form and the component.
