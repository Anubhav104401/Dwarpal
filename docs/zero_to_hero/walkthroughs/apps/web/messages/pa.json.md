---
fingerprint: 85d0f07974efa910
---
The public pages' words in **Punjabi** (ਪੰਜਾਬੀ), one of the eight languages added on 14 Nov 2026 (§7.15), with exactly the keys of the English file, line for line — a test (`i18n/messages.test.ts`) checks that no text is missing or empty and that every placeholder and tag survived translation. Punjabi is written in Gurmukhi, the script Punjabi is written in in India, and is spoken by about 33 million in India. Its letters come from the device's own fonts: Geist has none of them, and Windows, Android and iOS all ship a font for this script (`globals.css`).

!!! honest "Machine-drafted"
    These translations were drafted by the AI that wrote this code, not by a native speaker, and need a native speaker's review before real visitors read them — especially the privacy promises, the Aadhaar notice and the compliance map, where a word's shade of meaning matters.

Product names, the rules' official names and code stay as they are, and so does the brand, written in Latin letters: *Dwarpal*.

Every line holds the same text as the same line of the English file (see the English file's walkthrough), so the notes below are the same as Hindi's.

@@ 1
The file is one JSON object. Its top-level names are the **groups** of words (*namespaces*) that a page or component asks for, such as `useTranslations("Verify")`.

@@ 2-14
**`Language`** — the language menu's words: its name for screen readers (`label`), and each of the ten languages' own names, always written in that language and script — "English", "हिन्दी", "বাংলা", "मराठी", "తెలుగు", "தமிழ்", "ગુજરાતી", "ಕನ್ನಡ", "മലയാളം", "ਪੰਜਾਬੀ" — so a person who reads only one of them can still find theirs. Every language file names them identically (`messages.test.ts` checks).

@@ 15-18
**`Shell`** — the two promises under every verify-page screen.

@@ 19-22
**`Home`** — the home page. First its tab title and search-result description, and the name of the header's section links.

@@ 23-29
The header's section links, by the `id` of the section each leads to.

@@ 30-35
The console link, the badge, the motto, the opening paragraph, and the two buttons under it.

@@ 36-52
*How it works*: the section's title and lead, the "Step {number}" label (`{number}` is filled in by the page), and each step's title and text.

@@ 53-72
*The privacy promise*: the title and lead, then the four promises, each a title and its meaning.

@@ 73-76
*Accuracy, measured*: the title and lead (the table's own words are in `Accuracy`).

@@ 77-83
*For developers*: title, lead, the two code captions, and the note on the guides — whose `<code>…</code>` the page turns into code formatting (`t.rich`).

@@ 84-120
*Where it fits*: title, lead, the two column labels, the disclaimer, then for each place (`uk`, `eu`, `us`, `au`, `in`) its name, the rule's name, what it asks and how Dwarpal answers. The rules' own names stay as they are officially written. India's answer changed in Part 7: Aadhaar Secure QR is no longer "planned" — in test checks it can confirm an age, with its signature checked and only the date of birth read.

@@ 121-148
*Questions*: title, lead, and six questions, each with its answer (`q`, `a`). The answer to "I'm an adult and it wasn't sure" now says *an ID document* rather than naming the passport, since a test check offers Aadhaar first.

@@ 149-155
The closing invitation, and the footer.

@@ 156
The end of `Home`.

@@ 157-169
**`Accuracy`** — the live table's words: the message when the figures can't be loaded; the column headings; "not measured"; a share of an age band (`{share} of {ages}` — each language puts the parts in its own order); and the note under the table, with the model's version, dataset and photo count filled in.

@@ 170-185
**`Verify`** — the verify page: its tab title; loading; the problem screen's button and reference; the top-right label; the intro and its three promises; the camera button; the tries left; and "checking". Since D24 (8 Nov), also the intro's lead for a document-only check (`introLeadDocument`).

@@ 186-204
The four endings, each a title and a body; `{project}` and `{age}` are filled in. The step-up has a second body, `bodyAadhaar`, which a test session shows: confirm your age with your Aadhaar instead (§7.14).

@@ 205-235
The step-up's choices — `useDocument` for a live check, `useAadhaar` for a test one — and the leaving buttons; then the passport check: its title, three steps, photo button, and the selfie's line. Then, since 14 Nov, the same for **Aadhaar**, which a test check asks for first (§7.14): its title, three steps (the QR code's picture; the selfie; what is checked, read and never kept), `aadhaarChoice` — that Aadhaar is a choice and a passport works just as well, the **notice** the law expects before Aadhaar is used (§7.10) — the picture button and the selfie's line. Since Phase 9, the **Age Pass**'s words: the offer before the camera (its title, what the pass shows and the button), the notice when a pass is refused, and after a passed check the offer to save passes, the button while saving, the confirmation with how many and until when, and the failure. Since 9 Nov (decision D43), on a computer: the button for its webcam, and the file chooser's words beside it.

@@ 236-248
**`Camera`** — the camera screen: the landmarker's guidance, the starting message, the progress and colour messages, and the button.

@@ 267-294
**`Tips`** — one tip per reason code the API can give (`advice.ts` chooses), plus the general one (`default`) and the unusable-file tip of the document check. Since 9 Nov also a camera that couldn't be opened for the document. Since Part 7, three for an Aadhaar Secure QR: unreadable, not signed by UIDAI, and not accepted in a live check; and since 14 Nov `aadhaar_or_mrz_not_found`, which a test check shows instead of the passport-only tip when neither an Aadhaar code nor a passport's lines were found.

@@ 295-336
**`Problems`** — one message per problem that stops the check, each a title and a detail, plus the general one. Since 9 Nov also `rate_limited`: too many requests from one network, so wait a minute and reload.

@@ 337
The end of the file.

@@ 249-254
The three pose instructions, by the pose's code.

@@ 255-266
**`DocumentCamera`** (decision D43, 9 Nov) — the document camera's words: starting; the picture's name for screen readers; where to hold the document; that the picture isn't mirrored; the button that takes the photo; the question to ask of it; its description; and the buttons to use it, take it again, or choose a file instead.
