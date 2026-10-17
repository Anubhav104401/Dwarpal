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
| **[5](#part-5-building-it-file-by-file)** | Building it — every file, every line, in the order it was built | the main event | 🟡 Phase 0 complete (§5.0); grows each phase |
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
