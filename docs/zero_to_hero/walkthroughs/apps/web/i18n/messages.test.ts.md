---
fingerprint: 03e04b2ef4af3ae2
---
Tests for the words files (added on 14 Nov 2026, §7.15): every language other than English must have exactly English's texts, none empty, with every placeholder and tag intact — and every file must name the ten languages the same way. With ten files of 233 texts each, a missing comma's worth of mistake would otherwise reach a visitor as a broken page, or as a raw `{project}` on screen.

@@ 1-2
Node.js's file reading and path joining: the test reads the JSON files from disk.

@@ 4
Vitest's building blocks.

@@ 6
The list of languages, so a new one is tested the moment it is added.

@@ 8
**`Messages`** — the shape of a words file: names mapped either to a text or to another group of the same shape. A type that refers to itself like this is called **recursive**.

@@ 10-12
**`read`** — one language's file, parsed. `__dirname` is this test file's folder; the files are one level up, in `messages/`.

@@ 14-27
**`flatten`** — turn the nested groups into one flat list of paths and texts, such as `Verify.tries` → the text. A text is kept as it is; a group is flattened in turn (the function calls itself) with its name added to the path. A **Map** keeps them in order and lets the test look each path up.

@@ 29-32
**`placeholders`** — the names a text fills in. A **regular expression** finds every `{` followed by a name and then `,` or `}`: so `{count}` and `{count, plural, …}` count, but the words inside a plural's branches — `{Last try}` — don't, since a space follows `Last`. The names are sorted, so their order in the sentence doesn't matter: languages put words in different orders.

@@ 34-37
**`tags`** — rich-text tags such as `<strong>…</strong>`, which the page turns into elements. A translation that lost one would show the tag's text instead.

@@ 39
English's texts, read once: the reference every other file is compared with.

@@ 41-42
**`describe.each`** — the same tests, once per language except English; `%s` puts the language's code into each group's name, so a failure says which file.

@@ 44-47
**Test — the same texts, none empty**: the sorted paths must equal English's exactly (nothing missing, nothing extra), and no text may be blank.

@@ 49-55
**Test — every placeholder and tag kept**: for each English text, the translation must fill in the same names and carry the same tags. The second argument to `expect` (`path`) is printed if it fails, so the message names the exact text.

@@ 56
The end of the per-language group.

@@ 58-66
**Test — the language menu**: English names every language, and every file gives each language the very same name — its own name in its own script — so a person sees "தமிழ்" for Tamil whatever language the page is in.
