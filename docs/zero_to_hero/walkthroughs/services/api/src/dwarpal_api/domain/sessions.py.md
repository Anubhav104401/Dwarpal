---
fingerprint: 5c99f47ed30987f4
---
A **verification session** is one person's journey through one age check, from the moment a website asks for it until it ends. This file describes that journey as a **state machine**: a small set of **states** (statuses), and the list of **moves** allowed between them.

```
                ┌──────────── retry ────────────┐
                ▼                               │
 created ──► in_progress ───────────────────────┘
    │            │  └─────── step up ──────► awaiting_step_up
    │            │                                  │
    │            └──── pass / fail / reject ──► completed ◄──── (stronger check, Phase 6)
    │
    └──── (any open state) ──► expired  or  canceled
```

!!! kid "Explain like I'm six — a board game"
    In a board game, you can only move along the arrows: from START to square 1, from square 1 to square 2… You can't jump from FINISH back to START. A state machine is the rulebook of arrows. If the program ever tries an illegal jump — say, reopening a finished check to try again — the rulebook stops it on the spot.

Why bother with an explicit list? Without one, a status is just a text field that any line of code could set to anything. Bugs such as "a completed session went back to in-progress, and a second attempt overwrote the first result" become possible. With the list, every move goes through one function, `move`, which refuses anything not on it.

@@ 1
The docstring: the life of a session, as a state machine that only allows legal moves.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`datetime` for expiry times, and `StrEnum` for the statuses (see `Outcome` in `decision.py`).

@@ 8
The decision outcomes, because each outcome decides the session's next status (`STATUS_AFTER` below).

@@ 11-17
**`Status`** — the six states:

- `created` — the website has created the session; nobody has opened the link yet;
- `in_progress` — the person has opened the verify page and is taking the check;
- `awaiting_step_up` — the face check was too close to call; a stronger method is needed;
- `completed` — there is a final answer: pass, fail or reject;
- `expired` — the time limit ran out first;
- `canceled` — stopped on purpose (by the website, in a later phase).

@@ 20
**`ALLOWED`** — the rulebook: for each status, the set of statuses it may move to. A `frozenset` is a set that can never be changed, so the rulebook can't be edited while the program runs.

@@ 21
From `created`: the person starts, or the session expires or is canceled.

@@ 22-24
From `in_progress`: stay in progress (a retry), wait for a step-up, complete, expire or be canceled. "Stay" is listed explicitly, because a retry *is* a move — just to the same square.

@@ 25
From `awaiting_step_up`: complete (after the stronger check, Phase 6), expire, or be canceled.

@@ 26-29
The three **final** states allow no moves at all — an empty set. A finished check stays finished for ever. The closing brace ends the rulebook.

@@ 30
`OPEN` — the statuses in which a session is still alive, and can therefore still expire.

@@ 31-37
**`STATUS_AFTER`** — where a face attempt's outcome sends the session:

- pass, fail or reject → `completed`;
- step up → `awaiting_step_up`;
- retry → stays `in_progress`.

Writing it as a table, rather than a chain of `if` statements, puts the whole policy in one place where it can be read at a glance — and the test of `move` covers every row.

@@ 40-41
`IllegalTransitionError` — the error for a forbidden move. Its docstring gives the classic example.

@@ 44-47
**`move`** — the only way a status changes. If `target` isn't in the allowed set for `current`, raise the error, naming both. Otherwise return `target`, which the caller stores. Code elsewhere always writes `row.status = move(old, new)`, never `row.status = new` directly.

@@ 50-51
**`is_expired`** — has this session run out of time? Only if it is still **open** *and* the current time has reached its expiry time. A completed session never expires — its answer stays valid. Note that the current time is passed in as `now`: the domain never reads the clock itself, so a test can ask "what if it were 10 o'clock?" without waiting until 10 o'clock.
