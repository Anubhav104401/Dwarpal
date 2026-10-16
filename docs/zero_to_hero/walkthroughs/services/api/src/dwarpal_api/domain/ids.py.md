---
fingerprint: e60a82d4f538ee3d
---
Every session, project, attempt and token needs an **identifier**: a name that points at exactly one thing, for ever. This file makes them, in two forms:

- **inside** the system, an identifier is a **UUID** — a 128-bit number, so large that two randomly made ones practically never collide;
- **outside**, in the API and in links, it is written as short, safe text with a **type prefix**: `vs_01JA8XQ2MZ5BWP7C4TGN0R9K3D` for a verification session, `prj_…` for a project.

!!! kid "Explain like I'm six — library books"
    Every book in a library gets a sticker with a number. Two rules make the stickers useful: no two books ever share a number, and the numbers tell you roughly *when* each book arrived — so new books sit at the end of the shelf. The prefix is like the sticker's colour: blue for books, red for DVDs. Hand the librarian a red sticker when they asked for a book, and they notice straight away.

**Why UUID version 7?** The newest UUID standard (RFC 9562, 2024) defines a version whose first 48 bits are the **time of creation** in milliseconds, followed by random bits. That brings two advantages:

1. identifiers **sort by age**, which keeps database indexes tidy — new rows always land at the "end", like books on a shelf;
2. they still can't be **guessed**: the 74 random bits make it hopeless to predict someone else's session ID.

**Why prefixes?** The same idea used by large payment APIs: a `prj_` ID pasted where a `vs_` ID belongs is rejected immediately, instead of quietly looking up the wrong thing.

@@ 1
The docstring: time-ordered UUIDv7 values inside, prefixed text outside.

@@ 3
The project-wide type-hint setting.

@@ 5
`os` — here for `os.urandom`, which asks the operating system for **cryptographically secure** random bytes: unpredictable even to someone who has seen millions of earlier ones.

@@ 6
`uuid` — Python's built-in module for UUIDs. Python 3.14 adds a ready-made `uuid.uuid7()`, but this project runs on 3.13, so the six lines below build one by hand, exactly to the standard's layout.

@@ 8
`CROCKFORD` — the 32 symbols of **Crockford's Base32**: the digits and the capital letters *except* `I`, `L`, `O` and `U`. `I` and `L` look like `1`, and `O` looks like `0`, so a person reading an ID aloud or copying it by hand can't confuse them. Leaving out `U` makes it much less likely that an ID accidentally spells a rude word.

The symbols are in the same order as in the computer's character table, so **sorting the text sorts the IDs by time**, too.

@@ 9
`ENCODED_LENGTH = 26` — each Base32 symbol carries 5 bits, and 26 × 5 = 130 bits: just enough room for 128.

@@ 12-13
`InvalidIdError` — the error raised for malformed text. Writing `(ValueError)` makes it a special kind of Python's `ValueError`, so code that catches `ValueError` catches it too. The docstring is all it needs: an empty class body would be a syntax error, and a docstring counts as a body.

@@ 16
**`uuid7` — make a new UUIDv7.** The caller passes in the time (`unix_ms`: milliseconds since 1 January 1970). The domain never reads a clock itself (see `domain/__init__.py`).

The 128 bits are laid out like this:

```
 48 bits          4 bits   12 bits   2 bits   62 bits
┌────────────────┬───────┬─────────┬────────┬──────────────────────┐
│ time (ms)      │  7    │ random  │  10    │ random               │
└────────────────┴───────┴─────────┴────────┴──────────────────────┘
                  version           variant
```

The lines below use **bit operations**, which work on a number's binary digits:

| Operation | Meaning | Example |
| :-- | :-- | :-- |
| `a << n` | shift left by `n` places (multiply by 2ⁿ) | `0b1 << 3` = `0b1000` |
| `a >> n` | shift right by `n` places (divide by 2ⁿ, dropping the remainder) | `0b1000 >> 3` = `0b1` |
| `a & b` | keep only the bits that are 1 in **both** — a "mask" | `0b1101 & 0b0110` = `0b0100` |

The fourth operation is written with a vertical bar, `a | b`: it keeps the bits that are 1 in **either** number, so it *combines* them — `0b1000 | 0b0011` = `0b1011`.

`0b…` writes a number in binary and `0x…` in hexadecimal: `0xFFF` is twelve 1-bits.

@@ 17
Get 10 random bytes (80 bits) and read them as one big whole number.

@@ 18
`rand_a` — 12 of those random bits: shift the number right by 62, then keep the lowest 12 bits with the mask `0xFFF`.

@@ 19
`rand_b` — the lowest 62 random bits. `(1 << 62) - 1` is sixty-two 1-bits. (6 of the 80 random bits go unused.)

@@ 20
**Assemble the 128 bits**, each piece shifted to its place and combined with `|`:

- the time, cut to 48 bits, shifted up into the top 48;
- the **version** number `7`, in the next 4 bits;
- `rand_a`, in the next 12;
- the **variant** marker `0b10`, in the next 2 — it says "this UUID follows RFC 9562";
- `rand_b`, in the last 62.

@@ 21
Wrap the number in Python's `UUID` type, which knows how to print itself in the usual `0192a6f0-…` form and how to be stored in PostgreSQL.

@@ 24
**`encode` — UUID to prefixed text**, for example `encode("vs", value)`.

@@ 25-26
Take the UUID as one whole number, and start an empty list of symbols.

@@ 27-29
Repeat 26 times: take the lowest 5 bits (`number & 31`; 31 is five 1-bits), look up their symbol, then shift those 5 bits away (`>>= 5`). It is exactly how you'd write a number in base 32: peel off the last digit, again and again.

@@ 30
The digits came out *last first*, so reverse them, glue them together with `''.join(...)`, and put the prefix and an underscore in front.

@@ 33
**`decode` — prefixed text back to a UUID**, refusing anything malformed. It is the gatekeeper for every ID that arrives from outside.

@@ 34
`partition("_")` splits the text at the **first** underscore into three parts: before, the underscore itself, and after. If there is no underscore, the separator comes back empty.

@@ 35-36
Refuse the text unless it has an underscore, the expected prefix, and exactly 26 symbols after it. The message shows what a good ID looks like.

@@ 37
Start the number at zero.

@@ 38
Go through the symbols. `.upper()` means lowercase IDs are accepted too — people sometimes retype them.

@@ 39-41
`CROCKFORD.find(char)` gives a symbol's position, its value from 0 to 31, or `-1` if it isn't one of the 32 symbols. `{char!r}` shows the bad character in quotes in the error message.

@@ 42
The reverse of the peeling above: multiply what we have by 32 and add the new digit — exactly how you read the decimal number 472 as ((4 × 10) + 7) × 10 + 2.

@@ 43-44
26 symbols can hold 130 bits, but a UUID has only 128. If anything sits above bit 128 (`number >> 128` isn't zero), the text can't be a real ID, so it is refused instead of being silently cut short.

@@ 45
Return the UUID.
