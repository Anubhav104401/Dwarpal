# Dwarpal — Zero to Hero

**A book that takes you from "I have never written a line of code" to "I understand — line by line — how a real AI system that protects children online is designed, built, tested, deployed and defended."**

!!! kid "Explain like I'm six"
    Imagine a door to a room that only grown-ups are allowed to enter. Next to the door stands a guard. In old Indian temples the guard who stands at the door is called a **dwarpal** (द्वारपाल — *dwar* means "door", *pal* means "keeper").

    Our project builds a **computer guard for doors on the internet**. When someone tries to open a website that is only for grown-ups, the computer guard takes a quick look through the camera, makes a careful guess about whether the person is a grown-up, and then — this is the important part — **forgets the face immediately**. It only remembers "this person was allowed in" or "this person was not allowed in".

    This book teaches you everything needed to build that guard — starting from "what is a computer?"

## What this book is

This is a single, self-contained book about one project: an **AI-based age estimation system for protecting minors from accessing age-restricted online content**, code-named **Dwarpal**.

It is written for a reader who knows **nothing** about computers, programming, websites, servers or artificial intelligence. Every idea is introduced before it is used. Every word that might be new is explained the first time it appears, and again in the [Glossary](#glossary). Hover over words with a dotted underline (like API or HTTP) to see a short definition.

The book does three jobs at once:

1. **It teaches the foundations** — computers, the internet, websites, databases, servers, AI — from scratch.
2. **It records the thinking** — why this project is built the way it is, which alternatives were considered, and why they were rejected. In engineering, the *why* matters as much as the *what*.
3. **It explains every line of code** — every single line of every file in the project, in plain language, right next to the code itself.

## How to read it

| Part | What it covers | Read it if… | Status |
| :-- | :-- | :-- | :-- |
| **[0](#part-0-absolute-basics)** | Absolute basics — computers, files, programs, the internet, servers, websites, APIs, databases, hosting, Docker, Git, licences | you are new to computers or programming | ✅ written |
| **[1](#part-1-the-problem)** | The problem — why children need protecting online, what the laws say, why guessing age is hard, how people cheat | always — this is *why* the project exists | ✅ written |
| **[2](#part-2-ai-from-zero)** | AI from zero — data, models, training, neural networks, measuring mistakes | before the machine-learning chapters | 🗓 outline now; written alongside the AI phase |
| **[3](#part-3-thinking-before-building)** | Thinking before building — the problem analysis, the options we compared, the decisions, the detailed design, the architecture and the roadmap | always — this is *how* engineers think | ✅ Stages 1–5 written |
| **[4](#part-4-the-tools-one-by-one)** | The tools, one by one — Git, uv, Ruff, mypy, pytest, pnpm, Turborepo, Biome, Docker Compose, GitHub Actions; later FastAPI, PostgreSQL, Next.js, PyTorch, … | before the build chapters | 🟡 Phase 0 tools written; grows each phase |
| **[5](#part-5-building-it-file-by-file)** | Building it — every file, every line, in the order it was built | the main event | 🟡 Phases 0–3 (§5.0–5.3); Phase 4 under way (§5.4); grows each phase |
| **[X](#part-x-how-this-book-is-built)** | How this book itself is built — including its own code, line by line | you want to see the line-by-line format right now | ✅ written |
| **[Ledger](#coverage-ledger)** | A table, generated automatically, showing every code file and how much of it is explained | you want proof that nothing was skipped | ✅ automatic |
| **[Glossary](#glossary)** | Every technical word, in alphabetical order | whenever a word confuses you | ✅ growing |

**If you are completely new:** read Parts 0 → 1 → 3 in order, then Part X to see what a line-by-line explanation looks like. Parts 2, 4 and 5+ will appear as the project is built.

**Use the sidebar.** Press **Ctrl + K** (or **Cmd + K** on a Mac) to filter the table of contents. The **Theme** button switches between light and dark.

## The 60-second version of the project

1. A website that sells something grown-ups-only (or shows grown-ups-only content) needs to know whether a visitor is old enough. Laws in the UK, the EU, the US, Australia and India now *require* many websites to check this properly.
2. Asking "Are you 18? Yes/No" doesn't work — children just click "Yes".
3. Our system lets the website send the visitor to a **verification page**. The visitor looks at their camera for about three seconds and follows two or three random instructions ("turn your head left", "look up") while the screen glows softly in random colours.
4. On our **server**, an **AI model** estimates the visitor's age *as a range with a confidence level*, and checks that a real, live person was in front of the camera (not a photo, a video, or a video-game character).
5. A **decision engine** compares the estimate against the website's rule (for example "18+") using a carefully calculated safety margin. The answer is **pass**, **fail**, or **"not sure — please use another method"**.
6. The website receives a **digitally signed** answer — like a letter with a wax seal that cannot be forged — saying only "this person is over 18: yes". **It never receives the face, the estimated age, or the person's identity.**
7. The face images are **deleted from memory within about a second**. They are never saved anywhere.

## The boxes you will meet

Throughout the book, coloured boxes mark special kinds of explanation:

!!! kid "Explain like I'm six"
    The simplest possible version of an idea, usually a story or a comparison with everyday life.

!!! key "Key idea"
    Something important that later parts depend on. If you remember only one thing from a section, remember this.

!!! why "Why this choice?"
    The reasoning behind a decision.

!!! alt "Alternatives considered"
    Other ways we could have done it, and why we didn't.

!!! word "New word"
    A technical term being introduced. It's also in the Glossary.

!!! warn "Careful"
    A common mistake or trap.

!!! try "Try it yourself"
    Something you can type or click to see the idea working.

!!! real "Real world"
    A real event, law or product that shows why something matters.

!!! honest "Honest limitation"
    Something our system cannot do, or does not do perfectly. A good engineer says this out loud.

## The promise: every line explained — and how we *prove* it

Most explanations of software skip the "boring" lines. This book doesn't. Every source file in the project has a **walkthrough**: the code is shown on the left, and the explanation of each line (or small group of lines) on the right.

Promises are easy to break, so we made this one **checkable by a machine**. The program that builds this book:

- counts every non-empty line of every code file in the project, and marks which lines have an explanation;
- takes a **fingerprint** of each file when it is explained. If the code later changes, the fingerprint no longer matches and the book shows a red **"code changed since explained"** badge;
- prints a **[Coverage ledger](#coverage-ledger)** at the end of the book listing every file, how many of its lines are explained, and which files have not been explained yet.

You will learn exactly how that works — line by line — in [Part X](#part-x-how-this-book-is-built).

## Changelog of this book

| Date | What was added |
| :-- | :-- |
| 15 Oct 2026 | Front matter; Part 0 (absolute basics); Part 1 (the problem); Part 2 outline; Part 3 Stages 1–2 (analysis and options); Part X (how the book is built, with its own code explained line by line); coverage ledger; glossary |
| 15 Oct 2026 | Owner's decisions recorded (§3.6); Part 3 Stages 3–5: implementation design, architecture, roadmap (§3.7–3.9); 18 ADRs written |
| 15 Oct 2026 | **Phase 0 (foundations):** Part 4 (the tools of Phase 0); Part 5.0 (all 26 Phase 0 files walked through line by line); the builder gained snapshots and `--reanchor`, plus 9 tests; Part X updated. Coverage: 29 files, 994/994 lines |
| 16 Oct 2026 | **Phase 1 (walking skeleton), steps 1–3:** Part 4 gained §4.8–4.9 (web servers; pictures as numbers) and §4.10–4.14 (databases; Valkey; cryptography; API design; testing); §5.1.1 (the face side: contracts, vision library, inference service) and §5.1.2–5.1.3 (the API: rules, storage, signed tokens, endpoints), with every new file walked through; ADR-0019 and ADR-0020; the builder's re-anchoring rebuilt on difflib's edit operations, plus a check that every walkthrough is shown exactly once (14 tests). Coverage: 76 files, 3,425/3,425 lines |
| 16 Oct 2026 | **Phase 1, steps 4–5:** Part 4 gained §4.15–4.20 (TypeScript; React; Next.js; Tailwind CSS; the camera in a web page; Vitest and Playwright); §5.1.4 (the Node SDK, the verify page and the demo shop) and §5.1.5 (the end-to-end test with a fake camera), with every new file walked through; the builder now refuses walkthroughs that no chapter shows. Coverage: 123 files, 5,523/5,523 lines |
| 16 Oct 2026 | **Phase 2 (ML core), steps 1–2:** Part 2 §2.2 (data, labels and splits) and §2.14 (risk control and the Clopper–Pearson bound) written in full; §5.2.1 (the licence register, the fetch command and the unified manifest) and §5.2.2 (choosing the safety lines), with every new file walked through. Coverage: 130 files, 6,033/6,033 lines |
| 16 Oct 2026 | **Phase 2, step 3:** Part 2 §2.17 (faces: detection, landmarks, alignment) written in full; §5.2.3 (face preparation and duplicate removal), with every new file walked through. Coverage: 133 files, 6,404/6,404 lines |
| 17 Oct 2026 | **Phase 2, step 4:** Part 2 §2.1, §2.4–2.8, §2.10, §2.11 and §2.15 written in full (learning, models, loss, gradient descent, neural and convolutional networks, pre-training, distributions, over-fitting); §5.2.4 (training the age model), with every new file walked through; a 7-day cooldown for Python packages. Coverage: 138 files, 6,921/6,921 lines |
| 17 Oct 2026 | **Phase 2, step 4 (continued):** pretrained ConvNeXt-Tiny weights pinned in the model register and fine-tuned (band-MAE 1.84, the best so far); a real over-fitting curve in §5.2.4. Coverage: 138 files, 7,016/7,016 lines |
| 17 Oct 2026 | **Phase 2, step 5:** Part 2 §2.12 (measuring mistakes), §2.13 (calibration) and §2.16 (fairness) written in full; §5.2.5 (evaluation, release gates, and the first test-split result — one gate failed), with every new file walked through. Coverage: 141 files, 7,320/7,320 lines |
| 17 Oct 2026 | **Phase 2, step 6:** UTKFace approved for exact-age measurement; §5.2.6 (exact ages and the safety lines: the first risk-controlled thresholds, checked on unseen faces), with every new and changed file walked through. Coverage: 143 files, 7,667/7,667 lines |
| 17 Oct 2026 | **Phase 2, step 7:** Part 2 §2.19 (making models fast); §5.2.7 (from trained model to served model: ONNX export, parity, the registry manifest, the ONNX backend), with every new and changed file walked through. Coverage: 146 files, 8,080/8,080 lines |
| 17 Oct 2026 | **Phase 3 (liveness and anti-spoofing):** Part 2 §2.18 (liveness and anti-spoofing) written in full; §5.3 (the server's random challenge, the verify page's guidance and challenge with MediaPipe, the pose, light and injection evidence, the decision, the red-team tests, the labels test mode, and the plan for measuring genuine attempts), with every new and changed file walked through. Coverage: 153 files, 9,163/9,163 lines |
| 17 Oct 2026 | **Phase 3 (continued), genuine attempts:** §5.3 updated with six rounds of the owner's measurements — poses measured from the person's own frontal angles, a live pose meter and three photos per pose, a second face counted only if it is a separate person, 3–4 poses with turns deciding and look-up recorded — and the demo shop's Leave the cellar button, with every changed file walked through. Coverage: 153 files, 9,361/9,361 lines |
| 20 Oct 2026 | **Phase 3, red team:** §5.3.7 (the owner attacks their own system with posed selfies and videos on a phone); the anti-spoofing layer filled with MiniFASNet (converted to ONNX, run by OpenCV) and deciding; the head measured by a server-side face mesh; a hand detector, screen-pattern and mid-turn measures recorded; per-device attempt budgets; the page's photo timing fixed; Part 2 §2.18 updated; every new and changed file walked through. Coverage: 160 files, 10,176/10,176 lines |
| 24 Oct 2026 | **Phase 3, hardening:** live sessions require the anti-spoofing verdict, and `/readyz` reports whether the networks are loaded (§5.3.4); the ML tests run in their own process (`tasks.py`), after an intermittent crash when PyTorch was imported beside OpenCV and ONNX Runtime. Coverage: 160 files, 10,199/10,199 lines |
| 24 Oct 2026 | **Phase 4 (platform), step 1:** §5.4 and §5.4.1 (organisations, and row-level security: a restricted database role, a tenant named in every unit of work, a policy on every tenant table, and the tests that prove isolation — including the one that failed first); the new migration walked through, and every changed file re-explained; five glossary terms. Coverage: 161 files, 10,493/10,493 lines |
| 25 Oct 2026 | **Phase 4, step 3:** §5.4.2 (idempotency with sealed replies, a token-bucket rate limit, cursor pagination, scoped keys with rotation and revocation, and policy versions that never change); five new walkthroughs, every changed file re-explained; six glossary terms. Coverage: 166 files, 11,094/11,094 lines |
| 25 Oct 2026 | **Phase 4, step 4:** §5.4.3 (events and webhooks: the transactional outbox, the SSRF guard, signed deliveries and their retry schedule, the delivery worker, token introspection, and webhook verification in the Node SDK); nine new walkthroughs, every changed file re-explained; six glossary terms. Coverage: 175 files, 11,972/11,972 lines |
| 25 Oct 2026 | **Phase 4, step 5:** §5.4.4 (a hash-chained audit log per organisation and its verifier, retention periods with a purge and a sweep for abandoned sessions, and analytics from daily counts); five new walkthroughs, every changed file re-explained; two glossary terms. Coverage: 180 files, 12,458/12,458 lines |
| 26 Oct 2026 | **Phase 4, steps 2 and 6:** §5.4.5 (people: Argon2id passwords, sessions, one-time codes, CSRF protection, roles) and §5.4.6 (the published OpenAPI document, its drift test, and Schemathesis contract tests — and the bugs they found); seven new walkthroughs, every changed file re-explained; six glossary terms. Coverage: 187 files, 13,376/13,376 lines |
| 26 Oct 2026 | **Phases 6 and 7 begin:** §5.6.1 (reading the machine-readable zone of passports and ID cards: ICAO check digits, careful OCR repair, the age rule) and §5.7.1 (failing closed when a dependency is down; security headers on every API answer); three new walkthroughs, three re-explained. Coverage: 190 files, 13,733/13,733 lines |
| 26 Oct 2026 | **Phase 5 begins:** §5.5.1 (the console's first pages: signing in and up, organisations, members, API keys shown once, the audit log with its chain badge — the page hides, the API decides); eight new walkthroughs, four re-explained. Coverage: 198 files, 14,534/14,534 lines |
| 26 Oct 2026 | **Phase 5, project pages:** §5.5.2 (a project's sessions, decision traces, counts and policies, for test or live data; the check that the project belongs to the organisation named); two new walkthroughs, eight re-explained. Coverage: 200 files, 15,182/15,182 lines |
| 26 Oct 2026 | **Phase 5, webhooks in the console:** §5.5.3 (a project's endpoints, test events, deliveries and replays; the webhook use cases now name any actor, a key or a person; analysts can't see where events go); one new walkthrough, eleven re-explained. Coverage: 201 files, 15,628/15,628 lines |
| 27 Oct 2026 | **Phase 5, security and members:** §5.5.4 (setting up one-time codes in the console; changing members' roles and removing members, with an owner always kept — and the row locks that make that hold when two requests race; text the database can't store refused with `422`, a bug found by the contract tests); two new walkthroughs, nine re-explained. Coverage: 203 files, 16,006/16,006 lines |
| 27 Oct 2026 | **Security update:** Next.js upgraded from 16.4.0 to 16.4.2 in both web apps, closing two critical remote-code-execution flaws and a denial-of-service flaw; the package walkthroughs updated. Coverage: 203 files, 16,006/16,006 lines |
| 27 Oct 2026 | **Phase 5, exit tests:** §5.5.5 (browser tests on Chromium, Firefox and WebKit; axe accessibility checks against WCAG 2.2 AA; Lighthouse scores; a QR code for one-time codes — and the faint text, cramped checkboxes, cookie and search-engine findings they produced); three new walkthroughs, thirteen re-explained. Coverage: 206 files, 16,191/16,191 lines |
| 27 Oct 2026 | **Phase 5, design system:** §5.5.6 (OKLCH tokens — a midnight-indigo ink scale with zinc's lightness, saffron, teal — Geist Sans and Mono, a type scale, motion presets, shared components, and a specimen page checked in light and dark); two new walkthroughs, fifteen re-explained. Coverage: 208 files, 16,393/16,393 lines |
| 27 Oct 2026 | **Lighthouse CI fixes:** four patched dependencies forced with pnpm overrides (decision D14). Coverage: 208 files, 16,399/16,399 lines |
| 27 Oct 2026 | **Phase 7, scans, traces and load:** §5.7.3 (pip-audit, Trivy and ZAP run and triaged; OpenTelemetry traces with nothing about the person; a Locust load test that first measured refusals, then the truth — 4.5 s per attempt against a 1.5 s target); seven new walkthroughs, nine re-explained. Coverage: 215 files, 16,781/16,781 lines |
| 28 Oct 2026 | **Phase 7, performance and Semgrep:** §5.7.4 (the age model sees the 3 sharpest frames, checked against the certified lines on 11,301 faces; INT8 tried and rejected; a laptop throttling its background work; a one-second queue; the load test re-run at stress and realistic paces; Semgrep run, its findings fixed or reviewed); one new walkthrough, eleven re-explained. Coverage: 216 files, 16,995/16,995 lines |
| 29 Oct 2026 | **Decision P2, and switching webhooks off:** NFR-05's load settled as 50 people in a check (§5.7.4); webhook endpoints can be switched off and on, from the website API and the console (§5.5.3); nine re-explained. Coverage: 216 files, 17,116/17,116 lines |
| 29 Oct 2026 | **Searching sessions:** by outcome and by the website's own reference, in the API and the console (§5.5.2); nine re-explained. Coverage: 216 files, 17,225/17,225 lines |
| 29 Oct 2026 | **A browser test of the member controls** (§5.5.4); one re-explained. Coverage: 216 files, 17,256/17,256 lines |
| 29 Oct 2026 | **Recovery codes, and switching one-time codes off** (§5.5.4): ten single-use codes stored as HMACs (migration 0008); turning codes off needs the password and a current code; one new walkthrough, ten re-explained. Coverage: 217 files, 17,499/17,499 lines |
| 29 Oct 2026 | **Phase 7, a script policy with a nonce:** §5.7.5 (the web app's content security policy is made per page by `proxy.ts`, allowing only scripts with that page's nonce — ZAP's last real warning); two new walkthroughs, three re-explained. Coverage: 219 files, 17,575/17,575 lines |
| 29 Oct 2026 | **Phase 7, pulling the plug under load:** §5.7.6 (Valkey, PostgreSQL and inference stopped during a load test: nothing passed, all recovered; one 500 — a database lost mid-query — now answered 503); one new walkthrough, one re-explained. Coverage: 220 files, 17,611/17,611 lines |
| 29 Oct 2026 | **Phase 7, metrics, a dashboard and alerts:** §5.7.7 (request totals labelled by route pattern, sent through the collector to Prometheus; burn-rate alerts on the 99.9 % promise and NFR-05; a Grafana dashboard kept as a file); four new walkthroughs, six re-explained. Coverage: 224 files, 17,813/17,813 lines |
| 29 Oct 2026 | **The counts as a chart** (§5.5.2): 30 days of finished checks as bars stacked by outcome, in colours checked for colour-blind readers, with each day's numbers on hover or focus and as a table; three new walkthroughs, three re-explained. Coverage: 227 files, 18,020/18,020 lines |
| 29 Oct 2026 | **The age model's page** (§5.5.2): which model decides, whether it may decide live checks, what it learnt from, and its lines with their measured worst cases, for anyone signed in (`GET /console/v1/model`); two new walkthroughs, nine re-explained. Coverage: 229 files, 18,334/18,334 lines |
| 29 Oct 2026 | **A sidebar and a command palette** (§5.5.6): the console's places beside every signed-in page, and ⌘K/Ctrl+K to search organisations, projects and pages, built on the browser's modal dialog; three new walkthroughs, nine re-explained. Coverage: 232 files, 18,571/18,571 lines |
| 29 Oct 2026 | **The face checks' figures** (§5.5.2): the median time to a decision (as a band of seconds, against the 15 s target), and the shares rejected as likely attacks and sent to a stronger check, from new daily counts that keep no one's exact time; four new walkthroughs, eight re-explained. Coverage: 236 files, 18,830/18,830 lines |
| 30 Oct 2026 | **Chaos tests** (§5.7.6): PostgreSQL, Valkey and inference die in the middle of a check — through a TCP relay the test can cut — and nothing passes, then the check recovers; they found that uploaded frames were never closed (now closed as the request ends, in both services). `body-parser` 1.20.9 added to the overrides. Four re-explained. Coverage: 236 files, 18,978/18,978 lines |
| 30 Oct 2026 | **The check in a modal** (§5.5.7, decision D16): the browser SDKs `@dwarpal/js` and `@dwarpal/react`; a verify page may be framed only by the website its session returns to, and talks to it only with `postMessage`; the shop opens the check over its own page. Fourteen new walkthroughs, fifteen re-explained. Coverage: 250 files, 19,640/19,640 lines |
