---
fingerprint: c1067501b3d71e08
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

@@ 10-13
`itertools` (to try combinations of repairs), `dataclass`, `date`, and `Literal`.

@@ 15
`FILLER` — the `<` that pads every field and stands for spaces.

@@ 16
`WEIGHTS` — the check digit's weights, 7, 3, 1, repeated along the field.

@@ 17-19
OCR engines confuse some letters and digits: `O` and `0`, `I` and `1`, `S` and `5`, `B` and `8`, and a few more. The two dictionaries say which digit a look-alike letter stands for, and the other way round.

@@ 20
`MAX_REPAIRS` — a field with more than four doubtful characters is too damaged to guess at: guessing among too many combinations could make a wrong reading pass by chance.

@@ 22-23
The three layouts, by name, and their shapes: lines and characters per line.

@@ 26-31
**`MrzError`** — a zone that can't be trusted, with a stable `code` (`mrz_unreadable`, `mrz_check_failed`, `mrz_date_unknown`, `mrz_date_invalid`) and a sentence saying which part failed.

@@ 34-41
**`MrzDocument`** — everything that leaves the module: the layout, the document type (`P` for a passport), the issuer's three-letter code, the date of birth, the expiry date, and the fields that were repaired.

@@ 43-46
**`birth_year_month`** — all of the date of birth that Dwarpal stores. The full date is used for the age decision, then dropped.

@@ 49-57
**`value`** — a character's value for check digits: digits are themselves, `A` to `Z` are 10 to 35, and `<` is 0. Anything else can't appear in a zone.

@@ 60-62
**`check_digit`** — ICAO's rule: multiply each character's value by 7, 3, 1, 7, 3, 1, … in turn, add them up, and keep the last digit. Because 7, 3 and 1 share no factor with 10, changing any single **digit** always changes the result: no misread digit goes unnoticed.

@@ 65-67
**`_candidates`** — the readings an OCR mistake might hide.

@@ 68-69
In a field that may hold only digits (dates, check digits), every look-alike letter can only have been a digit.

@@ 70-73
In a field that may hold both (a document number), each doubtful character could be either. If there are too many, give up.

@@ 74
Every combination: `itertools.product` takes one choice from each character's set of possibilities, in all possible ways.

@@ 77-78
**`checked`** — the field, if its check digit agrees; otherwise its one repair that makes it agree; otherwise an error.

@@ 79
A check digit read as a look-alike letter is first turned back into a digit.

@@ 80-81
An optional field left empty may have an empty check digit too.

@@ 82-84
The ordinary case: a readable field whose check digit agrees.

@@ 85-88
Otherwise, try every repair. Accept only if **exactly one** repair makes the check pass, and record that the field was repaired. If two different repairs both pass, the zone is ambiguous, and guessing would be dangerous.

@@ 89
No repair works: the check digit doesn't match.

@@ 92-95
**`_date`** — split `YYMMDD` into numbers; a date with unknown parts (`<<`, which ICAO allows) can't be used for an age decision.

@@ 98-102
**`_real_date`** — make a real date, refusing impossible ones such as 31 February.

@@ 105-110
**`birth_date`** — a zone writes years with two digits, so the century must be inferred: the most recent one that doesn't put the birth in the future. `74` becomes 1974; `08` becomes 2008; and `26` becomes 1926 if 2026's date hasn't arrived yet.

@@ 113-117
**`expiry_date`** — expiries are in this century, unless that would be more than 50 years ahead: no document lasts that long.

@@ 120-124
**`layout`** — which of the three layouts the lines have, or an error.

@@ 127-129
**`parse`** — read a zone and return only what an age check needs.

@@ 130
Tidy the text: drop blank lines and stray spaces, and use capitals.

@@ 131-132
Find the layout; start the list of repairs.

@@ 133-135
**TD1** (ID cards): the document number and its check digit are on the first line, followed by the first optional field.

@@ 136-138
A document number longer than 9 characters doesn't fit. ICAO's rule: put `<` where its check digit would be, and continue the number in the optional field, followed by its check digit there.

@@ 139-141
Check the number, the date of birth and the expiry date.

@@ 142-143
The **composite** check digit covers almost the whole zone at once: the first line from the number on, the dates with their check digits, and the second optional field.

@@ 144
The document type and issuer.

@@ 145-147
**TD2 and TD3**: everything that matters is on the second line; they differ in where the optional field ends.

@@ 148-150
Check the number, the date of birth and the expiry date.

@@ 151-154
The optional field. On a passport (TD3) it holds a personal number, with its own check digit.

@@ 155-156
The composite check digit, over the number, the dates and the optional field, with their check digits; it sits last on the line.

@@ 157
The document type and issuer.

@@ 158-165
Return only the safe facts: the layout, the type and issuer without filler, the two dates with their centuries worked out, and the repairs.

@@ 168-171
**`age_on`** — whole years of age on a day: the years between, minus one if this year's birthday hasn't come yet. Someone born on 29 February has, in an ordinary year, not had their birthday on 28 February, so it comes on 1 March, as the law usually counts it.

@@ 174-176
**`age_outcome`** — the age rule for a document alone. The reasons record any repairs, so whoever reviews a decision can see what it rested on.

@@ 177
Each repaired field becomes a reason, such as `repaired_birth_date`.

@@ 178-179
An expired document fails, whatever the age.

@@ 180-182
Otherwise, old enough passes, and too young fails.
