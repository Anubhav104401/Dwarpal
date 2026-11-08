---
fingerprint: 0824b8cde43d35e4
---
The public pages' words in **English** (decision D2, §5.5.11): the home page and the verify page, gathered from the code into one file per language. The code names each piece of text by a key, such as `Verify.introTitle`; next-intl fills in the parts in braces — `Confirm you are {age} or over` — and, in `tries`, picks the plural form the language needs.

ICU message syntax treats `<` as the start of a tag, so the literal `<<<` of the MRZ is quoted: `'<<<'`.

@@ 1
The file is one JSON object. Its top-level names are the **groups** of words (*namespaces*) that a page or component asks for, such as `useTranslations("Verify")`.

@@ 2-6
**`Language`** — the language switch's words: its name for screen readers, and each language's own name (always written in that language: "English", "हिन्दी").

@@ 7-10
**`Shell`** — the two promises under every verify-page screen.

@@ 11-14
**`Home`** — the home page. First its tab title and search-result description, and the name of the header's section links.

@@ 15-21
The header's section links, by the `id` of the section each leads to.

@@ 22-27
The console link, the badge, the motto, the opening paragraph, and the two buttons under it.

@@ 28-44
*How it works*: the section's title and lead, the "Step {number}" label (`{number}` is filled in by the page), and each step's title and text.

@@ 45-64
*The privacy promise*: the title and lead, then the four promises, each a title and its meaning.

@@ 65-68
*Accuracy, measured*: the title and lead (the table's own words are in `Accuracy`).

@@ 69-75
*For developers*: title, lead, the two code captions, and the note on the guides — whose `<code>…</code>` the page turns into code formatting (`t.rich`).

@@ 76-112
*Where it fits*: title, lead, the two column labels, the disclaimer, then for each place (`uk`, `eu`, `us`, `au`, `in`) its name, the rule's name, what it asks and how Dwarpal answers. The rules' own names stay as they are officially written.

@@ 113-140
*Questions*: title, lead, and six questions, each with its answer (`q`, `a`).

@@ 141-147
The closing invitation, and the footer.

@@ 148
The end of `Home`.

@@ 149-161
**`Accuracy`** — the live table's words: the message when the figures can't be loaded; the column headings; "not measured"; a share of an age band (`{share} of {ages}` — each language puts the parts in its own order); and the note under the table, with the model's version, dataset and photo count filled in.

@@ 162-177
**`Verify`** — the verify page: its tab title; loading; the problem screen's button and reference; the top-right label; the intro and its three promises; the camera button; the tries left; and "checking". Since D24 (8 Nov), also the intro's lead for a document-only check (`introLeadDocument`).

@@ 178-195
The four endings, each a title and a body; `{project}` and `{age}` are filled in.

@@ 196-216
The step-up's choices and the leaving buttons, then the document check: its title, three steps, photo button, and the selfie's line. Since Phase 9, the **Age Pass**'s words: the offer before the camera (its title, what the pass shows and the button), the notice when a pass is refused, and after a passed check the offer to save passes, the button while saving, the confirmation with how many and until when, and the failure.

@@ 217-229
**`Camera`** — the camera screen: the landmarker's guidance, the starting message, the progress and colour messages, and the button.

@@ 230-235
The three pose instructions, by the pose's code.

@@ 236-258
**`Tips`** — one tip per reason code the API can give (`advice.ts` chooses), plus the general one (`default`) and the unusable-file tip of the document check.

@@ 259-296
**`Problems`** — one message per problem that stops the check, each a title and a detail, plus the general one.

@@ 297
The end of the file.
