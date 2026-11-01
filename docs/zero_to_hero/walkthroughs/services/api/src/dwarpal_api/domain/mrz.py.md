---
fingerprint: 0ae10c44bc3d8450
---
Reading the **machine-readable zone** (MRZ) of passports and ID cards (Phase 6, §5.6.1) — the two or three lines of `<`-filled capitals along the bottom of the photo page. The format is set by the International Civil Aviation Organization in **ICAO Doc 9303**, so it is the same in almost every country.

```
P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
L898902C36UTO7408122F1204159ZE184226B<<<<<10
```

Every important field is followed by a **check digit** — a digit computed from the field, so that a misread or tampered character is noticed. When a face check is unsure (*step up*, §3.7), a person may show a document instead; this module turns its zone into the few facts an age decision needs.

There are three layouts: **TD3** (passports: 2 lines of 44), **TD2** (2 of 36) and **TD1** (ID cards: 3 of 30). Reading the zone from a photo (finding the band, correcting perspective, OCR) needs software not yet installed; this module is the part that can be built and proved first — pure rules, checked against ICAO's own specimen documents.

!!! key "Key idea — read everything, keep almost nothing"
    The name, the document number and the nationality must be read, because the check digits cover them. But they leave this module only as a yes-or-no about the check digits. What comes out is the document's type and issuer, the dates, and which fields needed repair. Of the date of birth, Dwarpal keeps only the year and month.

@@ 1-6
The docstring, with the privacy rule.

@@ 8
The project-wide type-hint setting.

@@ 11-15
`itertools` (to try combinations of repairs and of readings), `math` (for `math.prod`, a product of counts), `dataclass`, `date`, and `Literal`.

@@ 17
`FILLER` — the `<` that pads every field and stands for spaces.

@@ 18
`WEIGHTS` — the check digit's weights, 7, 3, 1, repeated along the field.

@@ 19-32
OCR engines confuse some letters and digits: `O` and `0`, `I` and `1`, `S` and `5`, `B` and `8`, `T` and `7` (added in §5.6.2, after Tesseract read a `7` as a `T` on specimen photos), and a few more. The two dictionaries say which digit a look-alike letter stands for, and the other way round.

@@ 33
`MAX_REPAIRS` — a field with more than four doubtful characters is too damaged to guess at: guessing among too many combinations could make a wrong reading pass by chance.

@@ 38-39
The three layouts, by name, and their shapes: lines and characters per line.

@@ 42-47
**`MrzError`** — a zone that can't be trusted, with a stable `code` (`mrz_unreadable`, `mrz_check_failed`, `mrz_date_unknown`, `mrz_date_invalid`) and a sentence saying which part failed.

@@ 50-57
**`MrzDocument`** — everything that leaves the module: the layout, the document type (`P` for a passport), the issuer's three-letter code, the date of birth, the expiry date, and the fields that were repaired.

@@ 59-62
**`birth_year_month`** — all of the date of birth that Dwarpal stores. The full date is used for the age decision, then dropped.

@@ 65-73
**`value`** — a character's value for check digits: digits are themselves, `A` to `Z` are 10 to 35, and `<` is 0. Anything else can't appear in a zone.

@@ 76-78
**`check_digit`** — ICAO's rule: multiply each character's value by 7, 3, 1, 7, 3, 1, … in turn, add them up, and keep the last digit. Because 7, 3 and 1 share no factor with 10, changing any single **digit** always changes the result: no misread digit goes unnoticed.

@@ 81-83
**`_candidates`** — the readings an OCR mistake might hide.

@@ 84-85
In a field that may hold only digits (dates, check digits), every look-alike letter can only have been a digit.

@@ 86-89
In a field that may hold both (a document number), each doubtful character could be either. If there are too many, give up.

@@ 90
Every combination: `itertools.product` takes one choice from each character's set of possibilities, in all possible ways.

@@ 93-94
**`checked`** — the field, if its check digit agrees; otherwise its one repair that makes it agree; otherwise an error.

@@ 95
A check digit read as a look-alike letter is first turned back into a digit.

@@ 96-97
An optional field left empty may have an empty check digit too.

@@ 98-100
The ordinary case: a readable field whose check digit agrees.

@@ 101-104
Otherwise, try every repair. Accept only if **exactly one** repair makes the check pass, and record that the field was repaired. If two different repairs both pass, the zone is ambiguous, and guessing would be dangerous.

@@ 105
No repair works: the check digit doesn't match.

@@ 108-111
**`_date`** — split `YYMMDD` into numbers; a date with unknown parts (`<<`, which ICAO allows) can't be used for an age decision.

@@ 114-118
**`_real_date`** — make a real date, refusing impossible ones such as 31 February.

@@ 121-126
**`birth_date`** — a zone writes years with two digits, so the century must be inferred: the most recent one that doesn't put the birth in the future. `74` becomes 1974; `08` becomes 2008; and `26` becomes 1926 if 2026's date hasn't arrived yet.

@@ 129-133
**`expiry_date`** — expiries are in this century, unless that would be more than 50 years ahead: no document lasts that long.

@@ 136-140
**`layout`** — which of the three layouts the lines have, or an error.

@@ 143-145
**`parse`** — read a zone and return only what an age check needs.

@@ 146
Tidy the text: drop blank lines and stray spaces, and use capitals.

@@ 147-148
Find the layout; start the list of repairs.

@@ 149-151
**TD1** (ID cards): the document number and its check digit are on the first line, followed by the first optional field.

@@ 152-154
A document number longer than 9 characters doesn't fit. ICAO's rule: put `<` where its check digit would be, and continue the number in the optional field, followed by its check digit there.

@@ 155-157
Check the number, the date of birth and the expiry date.

@@ 158-159
The **composite** check digit covers almost the whole zone at once: the first line from the number on, the dates with their check digits, and the second optional field.

@@ 160
The document type and issuer.

@@ 161-163
**TD2 and TD3**: everything that matters is on the second line; they differ in where the optional field ends.

@@ 164-166
Check the number, the date of birth and the expiry date.

@@ 167-170
The optional field. On a passport (TD3) it holds a personal number, with its own check digit.

@@ 171-172
The composite check digit, over the number, the dates and the optional field, with their check digits; it sits last on the line.

@@ 173
The document type and issuer.

@@ 174-181
Return only the safe facts: the layout, the type and issuer without filler, the two dates with their centuries worked out, and the repairs.

@@ 276-279
**`age_on`** — whole years of age on a day: the years between, minus one if this year's birthday hasn't come yet. Someone born on 29 February has, in an ordinary year, not had their birthday on 28 February, so it comes on 1 March, as the law usually counts it.

@@ 282-284
**`age_outcome`** — the age rule for a document alone. The reasons record any repairs, so whoever reviews a decision can see what it rested on.

@@ 285
Each repaired field becomes a reason, such as `repaired_birth_date`.

@@ 286-287
An expired document fails, whatever the age.

@@ 288-290
Otherwise, old enough passes, and too young fails.

@@ 10
`dataclasses` (§5.6.2) — for `dataclasses.replace`, which copies a frozen dataclass with some fields changed: how a repaired reading gets its repair notes added.

@@ 34-36
Three settings for reading what OCR read from a photo (§5.6.2):
- `ALPHABET` — the 37 characters an MRZ may hold, tried one by one when a character is missing;
- `MAX_LENGTH_EDITS` — at most two characters may be dropped from a line, or one added;
- `MAX_READINGS` — a cap on the readings tried at once: a photo that would need more is too poor to guess at, and is better taken again.

@@ 184-191
**`_format_of`** — which layout OCR'd lines are meant to be, allowing for a character too many or too few: three lines are a TD1 card; two lines are a passport (44 characters) or a TD2 card (36), whichever the second line's length is closer to.

@@ 194-207
**`_resized`** — every way of making a text exactly `width` characters long with exactly `edits` changes. Too long: drop that many characters, in every combination (`itertools.combinations` lists the positions to drop). One too short: add each of the 37 characters at each position. Two too short is too much guessing, and gives nothing.

Why these slips? Tesseract reads long runs of the same character — the MRZ's `<<<<<<` fillers — badly, and splits or merges them.

@@ 210-220
**`_line_readings`** — the ways a data line could have read, with exactly `edits` changes, each with a flag saying how it was made:
- the whole line, resized (flag `False`);
- or its fixed fields (the first characters: number, dates, and their check digits), resized to their exact width, then fillers for an **empty optional field**, then the line's last characters (its final check digits) — flag `True`.

The second kind exists because optional fields are usually empty — rows of `<` — and that is exactly what OCR misreads most, as `6`, `K` or `E`. Whether "empty" was right is decided by the check digits, like everything else: the composite check digit covers the optional field, and the dates keep their own.

@@ 223-229
**`SKELETONS`** — for each layout and each of its data lines: how many characters of fixed fields it starts with, and how many check digits it ends with. A passport's (TD3) second line: 28 characters of number, nationality, birth date, sex and expiry with their check digits; the personal number between; then its check digit and the composite. A TD1 card has two data lines: its first ends without a check digit (0).

@@ 232-237
**`read_ocr`** (§5.6.2) — the parser's entrance for text read from a photo. Its docstring states the rule: the simplest reading that passes every check digit, and only if that reading is the **only** one.

@@ 238-242
Work out the layout and line width; which line holds the names (the third of a TD1 card, else the first); and replace that line with its first five characters — the document type and issuer — padded with fillers. The names are never looked at: the inference service already blanked them (§5.6.2), and this makes sure of it.

@@ 243-247
Try readings in rounds, by how many characters they change in all: **0** (the lines as read), then **1**, then **2**. Each round tries every way of sharing that total between the data lines (`split`) — for a TD1 card, 2 might be (2, 0), (1, 1) or (0, 2).

!!! key "Key idea — fewest changes first, and stop at the first round that works"
    A reading that needs no repair beats one that needs a repair, which beats one that needs two. The search stops at the first round with any passing reading, so a lucky but larger repair never outvotes a plainer one.

@@ 248-253
For each data line, its possible readings with that many changes; skip a combination too large to try (`MAX_READINGS`).

@@ 254-261
Try every combination: put the chosen line readings into the zone, and parse it with the ordinary parser — every check digit, with its own careful repairs. A combination that fails any check is simply not a reading.

@@ 262-264
A reading that passed: add notes saying how it was made — `line_length` if characters were dropped or added, `optional_fields_read_as_empty` if an empty optional field was assumed — to its repairs, which go into the decision's reasons.

@@ 265-268
Readings are grouped by what matters to an age check — layout, type, issuer, birth date and expiry. Different repairs that lead to the same document are one reading; of those, the one with the fewest repairs is kept.

@@ 269-273
After a round: **exactly one** document → that's the answer. More than one → refuse: the photo can't tell them apart, so neither is trusted. None → the next round; and after the last, refuse.
