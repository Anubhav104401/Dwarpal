# Part 3 — Thinking before building

## 3.1 How engineers think before they build

Nobody builds a house by buying bricks first. You first understand who will live there and what they need. Then you consider different kinds of houses, then draw the plans, then decide the order of work. Only then do you buy bricks.

This project follows five stages, in exactly that spirit:

| Stage | Question | Output | Where to read it |
| :-- | :-- | :-- | :-- |
| **1. Understand the problem** | What *exactly* must be solved, for whom, under which rules, and what makes it hard? | Problem analysis | §3.2, and the full version in `docs/design/01_problem_analysis.md` |
| **2. Consider solutions** | What are all the realistic ways to solve each part, and which is best — and why? | Options and recommendation | §3.3–3.6, full version in `docs/design/02_solution_options.md` |
| **3. Plan the implementation** | Now that the choices are confirmed, how exactly will each piece work? | Detailed design | after confirmation |
| **4. Design the architecture** | How do all the pieces fit, talk and fail safely? | Architecture documents and decision records | after confirmation |
| **5. Make a roadmap — and follow it** | In what order do we build, and how do we know each step is done? | Phased roadmap with exit criteria | after confirmation |

!!! key "Key idea — the confirmation gate"
    Between Stage 2 and Stage 3 there is a deliberate pause. The project owner reads the options and confirms (or changes) the key decisions *before* any real building starts. Changing a decision on paper costs minutes; changing it after 20,000 lines of code costs weeks.

## 3.2 Stage 1 in plain words — what we found

The full analysis is in `docs/design/01_problem_analysis.md`. Its main conclusions are below.

1. **This is a trust problem with an AI inside, not an AI problem.** A website must be able to *trust* a yes/no answer about age. The answer must be safe from forging and fair to everyone, and the website must never learn who the person is. A model on its own does none of that.
2. **The number that matters is the false-adult rate near the age limit**, not the average error. An average can look excellent while many 16- and 17-year-olds slip through.
3. **Free, downloadable age models are not safe enough.** In a 2026 benchmark, most of them called 39–100 % of minors "adults".
4. **Regulators accept face-based estimation — with conditions.** It needs a safety margin, a stronger second method for unclear cases, cheat-detection, fairness evidence and strong privacy.
5. **The hard parts are:**
    - **data** — few photos of teenagers exist, and most face datasets are "research only";
    - **cheating** — video-game faces already fooled a major platform;
    - **privacy** — faces are biometric data;
    - **fairness** — errors are uneven across groups;
    - **friction** — every extra second loses people.

The analysis also writes down precise **requirements** — 16 things the system must do and 15 qualities it must have, many with measurable targets. Some examples:

| Requirement | Target |
| :-- | :-- |
| Children aged 13–17 passing an "18+" check | at most **2 %** (goal); never more than **5 %** (a model above this cannot be released) |
| Adults aged 25+ passing without extra steps | at least **85 %** |
| Server time to process one check | under **1.5 seconds** on an ordinary 4-core server |
| Face images stored | **zero**, anywhere, ever |
| If anything inside breaks | the answer must **never** be "pass" (*fail closed*) |
| Lines of code explained in this book | **100 %** |

## 3.3 Stage 2 — the big choices, one by one

For each choice, we list the realistic options, compare them, and pick one. The full comparison tables are in `docs/design/02_solution_options.md`.

### Choice 1 — What shape is the product?

!!! kid "Explain like I'm six"
    Option A: give every website a "guard in a box" that runs inside the visitor's own browser. But then the *visitor* owns the guard — a clever child can simply tell it "say yes!".
    Option B: keep the guard in **our** building. The website sends visitors to our guard, and our guard sends the website a **sealed letter** with the answer.

| Option | Verdict |
| :-- | :-- |
| A guard that runs in the visitor's browser | ❌ Rejected — the visitor controls it, so the answer can be forged |
| **A hosted service websites connect to (B2B platform)** | ✅ **Chosen** — this is how professional age-check companies work, and what regulators audit |
| A parental-control app on the family computer | ➕ Possible later add-on |
| A tool that classifies *content* as adult or not | ❌ Different problem |

### Choice 2 — What tells us the age?

We compared face video, a single face photo, voice, hand photos, writing style, ID documents, digital-ID apps, and credit or email history.

**Chosen:** a **waterfall** — a few seconds of **face video** first; a **stronger method** (ID document or digital ID) only when the face estimate is too close to call.

!!! why "Why face video, not a single photo?"
    Several frames let us average away one bad frame. They also let us check that the face *moves the way we asked it to*, which proves a live person is there — something a single photo can never show.

### Choice 3 — Where does the AI run?

| Option | Problem | Verdict |
| :-- | :-- | :-- |
| Only in the browser | The browser belongs to the user → the result can be faked | ❌ |
| Only on our server | Works, but the user gets no live help ("move closer", "more light") → more failed attempts | ⚠️ |
| **Both:** the browser *guides*, the server *decides* | Best of both | ✅ **Chosen** |

!!! key "Key idea — the client guides, the server decides"
    The browser runs a small face-tracking model (MediaPipe) only to coach the user in real time. Nothing the browser says is *believed*. The server re-checks everything from the raw frames.

### Choice 4 — The AI model itself

We compared five approaches:

| Approach | What it is | Verdict |
| :-- | :-- | :-- |
| Download a ready-made free model | Quick | ❌ Unsafe — most call many minors "adults" |
| Pay a cloud company to guess ages | Quick | ❌ Faces leave our control; costs per check |
| Ask a giant general AI (like Gemini) | Surprisingly good on average | ❌ Faces leave our control; slow; still calls 16–29 % of minors "adults" |
| The best open research model (MiVOLO) | Strong | ➕ Used as the **benchmark to beat** |
| **Train our own specialist, starting from a strong pre-trained model** | Hard work | ✅ **Chosen** |

Our model will not answer "this person is 22". It answers with **a probability for every age from 0 to 100**: "probably 22; quite possibly 19–25; very unlikely to be under 17". From that one answer we can read off the chance that the person is over 13, 16, 18 or 21 — whatever the website needs.

#### The guard's line — calculated, not guessed

This is the most important idea in the design.

!!! kid "Explain like I'm six — the jar of photos"
    Imagine a jar holding 600 photos of real 17-year-olds, ones the model has never seen. We show every photo to our guard and count how many it would wrongly let in.

    Say 6 of the 600 get in. That's 1 %. But 600 is not infinity — maybe we got lucky with this jar. So we ask a careful maths question: *"Given that 6 of 600 got in, what is the **worst** the real rate could plausibly be?"* The answer, with 95 % confidence, is **1.96 %**.

    Our rule says "at most 2 %". 1.96 % is under 2 %, so this setting is allowed. If 7 of 600 had got in, the worst plausible rate would be 2.18 % — too high. Then we make the guard stricter and test again.

    With a smaller jar of only 300 photos, just **1** child getting through is the most we could accept. A smaller jar means more doubt, so the guard has to be stricter. **Less evidence forces more caution.**

The maths in the box is called a **Clopper–Pearson confidence bound**. Part 2 explains it properly. In engineering terms:

1. The website's policy states a **risk budget** — for example, "at most 2 % of 13–17-year-olds may pass, with 95 % confidence".
2. We test the model on held-out photos of children of *each* age (13, 14, 15, 16, 17), and of each group of people for which the test data has labels.
3. We choose the **least strict line that keeps the worst plausible pass rate under the budget for every one of those ages and groups**.
4. A second, lower line marks when we are confident someone is *under* the limit. Everyone between the two lines gets **step-up**, not a rejection.

!!! honest "Honest limitation"
    The guarantee holds for photos like the ones we tested with — mostly photos from public research collections. Real webcam pictures can be darker, blurrier and taken at stranger angles. We protect against that difference in four ways:

    - refusing poor-quality frames;
    - training on deliberately "webcam-ified" photos;
    - adding an extra safety margin;
    - watching the live pass rates for unexpected changes.

    But we say it out loud: **the guarantee is about the test photos, not a promise about every webcam on Earth.**

### Choice 5 — Finding the face

To estimate age we first have to find the face in the picture, and the eyes and nose inside the face. We compared several face finders and picked:

- **YuNet** on the server — small, fast, and MIT-licensed.
- **MediaPipe Face Landmarker** in the browser — it finds 478 points on the face in real time, which is how we can coach the user and track their head movements.

We rejected two popular alternatives because of their licences: one forbids commercial use, the other (AGPL) would force us to publish all our code under its terms. See §0.16.

### Choice 6 — Catching cheaters: an onion of defences

No single test catches every trick, so we stack independent layers. A cheater has to beat **all** of them at once.

| Layer | Catches |
| :-- | :-- |
| 1. **Picture quality check** — sharp? bright enough? exactly one face? big enough? | Garbage pictures, and people trying from far away |
| 2. **"Is it a real face?" model** (passive anti-spoofing) | Printed photos and phone screens |
| 3. **Random instructions** — e.g. "turn left, then look up" — different every time | Photos and pre-recorded videos |
| 4. **Screen-light check** — the screen glows softly in a random colour sequence, and a real face reflects it | Videos played to the camera, fake cameras, game characters (none can know the colours in advance) |
| 5. **Fake-camera clues** — suspicious camera names, robot-like timing | Software pretending to be a camera |
| 6. *(Later)* a detector for computer-generated faces | Game characters and 3D avatars |

!!! warn "Careful — safety for people with epilepsy"
    Rapidly flashing colours can trigger seizures in people with photosensitive epilepsy. The international accessibility rules (WCAG) require fewer than three flashes per second. Our screen-light check uses **slow, gentle colour changes** that stay well within those rules, and anyone can choose another method instead.

### Choice 7 — Making the decision

| Option | Verdict |
| :-- | :-- |
| "Pass if the guess is 18 or more" | ❌ About half of the 17-year-olds near the line would pass |
| "Pass if the guess is 25 or more" (a fixed buffer) | ⚠️ Safe, but many 18–24-year-olds blocked; the 25 is picked by hand |
| **A calculated line (Choice 4) with three answers plus step-up, and limited retries** | ✅ **Chosen** |

Every retry makes the guard stricter, so "try until it says yes" doesn't work. And if anything inside the system fails, the answer is "retry" or "step-up" — **never** "pass".

### Choice 8 — The stronger second method (step-up)

When the face check is unsure, the visitor needs another way to prove their age. All the options plug into the same "socket", so more can be added later:

- **ID document scan** — read the machine-readable lines at the bottom of a passport or ID card. Those lines include check digits, a little arithmetic trick that catches typing errors. A web browser can't read the passport's chip, so a well-made fake could fool this. We label it honestly as a *basic* check.
- **Aadhaar Secure QR** (India) — the QR code on Aadhaar is digitally signed by the government authority UIDAI, so the date of birth can't be forged. But Aadhaar data is sensitive and heavily regulated.
- **Digital ID apps** — such as the EU's age-verification app and digital wallets. Excellent and private, but still rolling out in 2026.

Which one we build first is one of the owner's decisions (§3.6).

### Choice 9 — Sending the answer: the wax seal

!!! kid "Explain like I'm six — the wax seal"
    Long ago, kings sealed letters with wax pressed by a special ring. Anyone could *read* the letter, but nobody could *forge* the seal without the ring. If the letter was changed, the seal broke.

    Our answer to the website is a letter like that, called a **signed token**. Our server has the secret "ring" (a **private key**). Anyone can check the seal using the matching **public key**, which we publish openly. A child can't write "over 18: yes" and fake the seal.

The letter is deliberately short. It says *who it's for* (which website), *when it expires* (minutes, not days), a *one-time number* so it can't be reused, and **"over 18: yes"**. It never contains the estimated age, a name, or any lasting identifier.

We rejected:

- returning the answer in the page address (`?result=pass`), because anyone can type that themselves;
- notifications without a seal, because anyone can fake them.

### Choice 10 — How the back-end programs are organised

!!! kid "Explain like I'm six — a restaurant kitchen"
    One cook doing everything gets overwhelmed. A thousand tiny kitchens are chaos. A good restaurant has **one main kitchen with clear stations** — starters, grill, desserts — plus a **special room** for the one job that needs heavy equipment.

| Option | Verdict |
| :-- | :-- |
| One big program doing everything (including the AI) | ❌ The AI's heavy maths would slow everything else down; faces and business data would mix |
| **One well-organised main program (the API) + a separate AI program (the inference service) + a background helper (the worker)** | ✅ **Chosen** |
| Dozens of tiny programs ("microservices") | ❌ Far too much to run and repair for a small team |

Inside the API, code is arranged in rings, which is called **hexagonal architecture**. In the centre are the **rules**: pure logic like "how do we decide?", which can be tested in milliseconds without any server. Around them are the **use cases** ("create a session", "submit frames"). On the outside are the **adapters** that talk to the web, the database and the AI service. The rules never depend on the outside, so the outside can change without breaking them.

### Choice 11 — Where things are remembered

| What | Where | Why |
| :-- | :-- | :-- |
| Websites, settings, sessions, results, audit trail | **PostgreSQL** | Reliable, transactional. Its *row-level security* keeps each customer's data separate even if our own code has a bug |
| Short-lived things: one-time challenge numbers, rate limits, background jobs | **Valkey** | Extremely fast; data can expire automatically. Chosen over Redis because of Valkey's simpler, permissive licence |
| AI model files | A versioned folder with a fingerprint for every file | So we always know exactly which model made which decision, and can roll back |
| **Faces** | **Nowhere** | There is no table, folder or log for them |

### Choice 12 — The websites people see

"Exceptionally beautiful" and "fast" are both requirements. The chosen tools — each explained fully in Part 4:

| Job | Tool |
| :-- | :-- |
| The website framework | **Next.js 16** with **React 19** and **TypeScript** |
| Styling | **Tailwind CSS 4**, with accessible components from **shadcn/ui** |
| Animation | **Motion**, plus **GSAP** and **Lenis** for scroll effects |
| 3D | **three.js** with **React Three Fiber** — a hero image made of the 478 face points, floating like stars |
| Camera AI in the browser | **MediaPipe Tasks Vision** |
| Charts in the dashboard | **Recharts** |
| Testing | **Vitest** and **Playwright** (which can feed a recorded video in as a fake webcam, so the whole flow is tested automatically) |

We considered SvelteKit, Nuxt, React Router, Astro and others. Next.js wins on ecosystem size, component libraries and deployment options. Part 4 explains the trade-offs.

### Choice 13 — Putting it on the internet

| Option | Monthly cost | Verdict |
| :-- | :-- | :-- |
| **One rented server running everything in Docker, with Caddy for automatic HTTPS** | €0 (free tier, if available) to about €8–15 | ✅ Recommended |
| Several free services glued together | €0 | ⚠️ Limits, sleeping servers, many vendors |
| Kubernetes (the system big companies use to run many servers) | €€ | ➕ We'll ship the configuration files for it, so it's possible later |
| Only on the laptop | €0 | Interim only — not "deployable" |

This is also an owner decision (§3.6).

### Choices 14–18 — Watching, protecting, improving and documenting

- **Watching (observability):** dashboards for speed, errors, the mix of pass/fail/step-up answers, and AI health. Logs never contain faces, keys or secrets — a test checks this.
- **Protecting (security):**
    - each customer's data is separated twice — in the code and in the database;
    - keys are shown once, stored only as fingerprints, and can be revoked;
    - passwords are hashed with Argon2id;
    - notifications to websites are signed;
    - there are limits on how fast anyone can call us;
    - the audit log is **tamper-evident**: each entry contains a fingerprint of the previous one, so changing history breaks the chain.
- **Improving the AI (MLOps):**
    - every model gets a version number, a test report and a "model card";
    - a new model is only released if it passes **release gates** — it must not let more children through, be less fair, or be slower than allowed;
    - new models first run silently next to the old one ("shadow mode") before taking over.
- **Testing:** small tests for every rule; tests against a real database; an automatic test of the whole camera flow with a fake camera; accessibility tests; load tests; cheating tests.
- **Documenting:** this book, decision records for every important choice, the API reference, the model card and a privacy impact assessment.

## 3.4 The whole design in one picture

```
   The website (shop)                 Dwarpal                                    
   ─────────────────                  ───────                                    
   shop server ── "please check" ───► API ──────────────► database (no faces)    
        ▲                              │  ▲                                       
        │  sealed answer               │  │ scores only                           
        └──────────────────────────────┤  │                                       
                                       ▼  │                                       
   visitor's browser ── few frames ──► API ──► AI service: find face → check      
   (camera page: guidance,                     quality → real or fake? → follow   
    random instructions,                       the instructions? → reflect the    
    gentle colour light)                       colours? → age probabilities       
                                               ─► frames forgotten                
```

The full technical diagram, and the step-by-step life of one check, are in §19 of `docs/design/02_solution_options.md`. They are rebuilt and explained in full in Stage 4.

## 3.5 What we said "no" to — and why

| Idea | Why not |
| :-- | :-- |
| Trusting the browser's answer | The user controls the browser |
| Sending faces to a big AI company for each check | The faces leave our control; it is slow and costs money; and it still lets many minors through |
| Training on photos scraped from social media | Illegal and unethical |
| Generating fake teenager photos with AI to train on | Research in 2026 found the generated faces don't look the age they're supposed to — the labels would be wrong |
| Guessing race or sex during checks "for fairness" | Unnecessary sensitive guessing; we measure fairness offline instead |
| Using AGPL or non-commercial components in the running system | Licence restrictions (§0.16) |
| Keeping encrypted copies of faces "just in case" | That *creates* the data leak we promise can't happen |

## 3.6 The confirmation gate — what the owner decided

On 15 October 2026 the project owner read Stages 1 and 2 and made four decisions:

| Question | Decision | What it means for the build |
| :-- | :-- | :-- |
| **Scope** | Platform + dashboard + demo shop | We build the full service *and* the console website owners use, *and* a fictional shop that uses it. The parental-control browser extension is left out of version 1 |
| **Step-up methods** | **Both** — the ID-document scan first, then Aadhaar Secure QR | Two real "stronger checks" will plug into the step-up socket: a worldwide one (passports and ID cards) and an India-specific one (the government-signed Aadhaar QR code) |
| **Where it runs** | One rented server running Docker Compose, with Caddy for HTTPS | Simple, cheap and real. We still write Kubernetes configuration files, so a bigger deployment remains possible |
| **Name** | **Dwarpal** | The door-guardian it is |

Every other recommendation in Stage 2 was accepted as proposed.

!!! key "Key idea — writing decisions down"
    Each important decision is now written up as a short **Architecture Decision Record** (ADR) in `docs/adr/`: what was decided, why, what else was considered, and what it costs us. Months later, when someone asks *"why on earth did they use Valkey instead of Redis?"*, the answer is one file away. Good teams treat their decisions as part of the project, not as memories.

    There are 18 ADRs, from ADR-0001 ("we write ADRs") to ADR-0018 ("which licences we allow"). `docs/adr/README.md` lists them all.

## 3.7 Stage 3 — How each piece will actually work

The full engineering version is `docs/design/03_implementation_design.md`. Here are its most important ideas in plain words.

### One house with many rooms (the monorepo)

All of Dwarpal lives in **one repository**, organised like a house:

| Room | What lives there |
| :-- | :-- |
| `apps/` | Things people visit: the website (marketing, verify page, dashboard) and the demo shop |
| `packages/` | Reusable JavaScript/TypeScript pieces: the design system, the camera helper, the SDKs websites install |
| `services/` | The two Python servers: the **API** (the brain office) and the **inference service** (the AI room) |
| `libs/` | Python code shared by several rooms. Most importantly, the face-straightening code — so the AI is trained and used on faces prepared in **exactly** the same way |
| `ml/` | Everything for teaching the AI: datasets, training, testing, the safety-line calculations |
| `models/` | The "ID cards" (manifests) of each trained model version |
| `infra/` | How to run it all: Docker, Caddy, monitoring, deployment scripts |
| `docs/` | Design documents, decision records, and this book |

!!! why "Why one repository instead of many?"
    When one change touches several rooms — say, a new score flowing from the AI room to the dashboard — it lands as **one** reviewed change. Separate repositories would have to be updated in lock-step, and they eventually drift apart.

### The life of a verification session

A **session** is one visit to the guard. It moves through a fixed set of states:

```
created → in progress → completed (pass / fail / reject)
                  ↘ awaiting step-up → completed
created or in progress → expired / canceled
```

These moves are enforced by a tiny program called a **state machine**. A session can't jump from "created" straight to "completed: pass", and once it is completed it can never change. Tests try every possible move to prove it.

### What is stored — and what never is

| Kind of data | Example | Stored? |
| :-- | :-- | :-- |
| Biometric | camera frames, face crops | **Never** — memory only, for about a second |
| Identity documents | name and passport number from an ID; Aadhaar details | **Never** — only "year and month of birth" survives from a document |
| Scores | "quality 0.92, live 0.98, P(over 18) 0.995" | Yes, for 90 days |
| Metadata | session status, which policy, timestamps | Yes, for 90 days |
| Secrets | password fingerprints, encrypted signing keys | Yes, protected |
| Audit trail | "admin X created API key Y at time Z" | Yes, for 1 year, tamper-evident |

Even the **disk is protected from accidents.**

- The programs that touch faces run on a **read-only** file system: they physically cannot write files.
- Their only scratch space is a **RAM disk** (`tmpfs`), which vanishes when the program stops.
- A special test sends a "canary" pattern of bytes through the system and fails if that pattern ever appears in any log.

### The decision engine, in order

When the AI room reports back, the guard's rulebook is checked **in this order**. The first rule that applies wins:

1. **Did anything go wrong?** — then *retry* (never *pass*).
2. **Were the pictures good enough?** — if not, *retry*, with a helpful hint like "find more light".
3. **Was it really a live person following the instructions?** — if clearly not, *reject*. If unclear, *step-up*.
4. **Did the frames agree with each other?** — if not, *retry*.
5. **The age line** — above the calculated pass line → *pass*; below the fail line → *fail*; in between → *step-up*. Each retry makes the pass line a little stricter.
6. **Too many tries?** — then only *step-up* or *fail* remain possible.

This rulebook is **pure**: it never touches the internet, a database or the clock — it just takes inputs and returns an answer. That makes it easy to test thousands of times with random inputs, checking promises such as *"a higher chance of being an adult can never turn a pass into a fail"* and *"missing information can never produce a pass"*.

### Teaching the AI: four jars of photos

!!! kid "Explain like I'm six — homework, practice tests, the ruler and the final exam"
    Imagine studying for an exam with four piles of questions:

    1. **Training jar** — the textbook exercises you practise on, again and again.
    2. **Validation jar** — practice tests that tell you when to stop studying and which study method works best.
    3. **Calibration jar** — a special test used for one thing only: drawing the guard's line (§3.3, "the jar of photos").
    4. **Test jar** — the **final exam**, taken once, at the very end. Nobody peeks at it while studying.

    If you studied *from* the final exam, your score would be meaningless. In AI this mistake is called **data leakage**, and keeping the four jars strictly apart is how we avoid it. If the same person's photos could land in two jars, the model would partly "remember" them, so we split **by person** wherever the data says who is who. Duplicate photos are also removed across all jars.

### Checking a passport's maths: the 7-3-1 check digit

At the bottom of every passport are two lines of code-like text: the **machine-readable zone (MRZ)**. Here is the second line of the official specimen passport published by ICAO (the UN agency that standardises passports). It belongs to the fictional *Anna Maria Eriksson* of the fictional country *Utopia*:

```
L898902C36UTO7408122F1204159ZE184226B<<<<<10
```

Hidden in it is the date of birth `740812` (12 August 1974), followed by a **check digit**, `2`. A check digit is a tiny piece of arithmetic that catches misreadings. Multiply the digits by the repeating weights **7, 3, 1**, add everything up, and keep the last digit:

| Character | 7 | 4 | 0 | 8 | 1 | 2 |
| :-- | --: | --: | --: | --: | --: | --: |
| Weight | 7 | 3 | 1 | 7 | 3 | 1 |
| Product | 49 | 12 | 0 | 56 | 3 | 2 |

49 + 12 + 0 + 56 + 3 + 2 = **122**, and the last digit of 122 is **2** — the check digit printed in the passport. If the camera misread a single digit, the sum would almost certainly come out different, and we would know.

Letters count too: A = 10, B = 11, … Z = 35, and the filler character `<` = 0. Our MRZ reader checks every check digit before believing a single date.

!!! honest "Honest limitation"
    Check digits catch *mistakes*, not *forgeries*: anyone can calculate a correct check digit for a fake date. Real passports also contain a chip with a digital signature, but web browsers can't read it. That's why Dwarpal labels the MRZ check honestly as **basic** assurance.

### The Aadhaar Secure QR: a government wax seal

The Secure QR code printed on Aadhaar documents contains the holder's details and photo, **digitally signed by UIDAI** — the same "wax seal" idea as our own tokens (§3.3, Choice 9). Dwarpal can check that seal using UIDAI's published public key, read only the date of birth, compare the QR's photo with a live selfie, and then forget everything. Because Aadhaar data is legally sensitive, the feature is off by default outside India, asks for explicit consent, stores nothing, and is marked as needing legal review before real-world use.

## 3.8 Stage 4 — How the pieces fit (architecture)

The full engineering version is `docs/design/04_architecture.md`.

!!! kid "Explain like I'm six — four zoom levels"
    Architects explain big systems the way a map app zooms in: first the **country** (who uses the system and what it talks to), then the **city** (the separate programs and how they connect), then a **building** (the parts inside one program), and finally a **room** (the code itself). This is called the **C4 model** — Context, Containers, Components, Code — and our architecture document follows exactly these four zoom levels.

**The city map — the separate programs (containers):**

| Program | Job | Can talk to |
| :-- | :-- | :-- |
| **Caddy** (the front gate) | Handles HTTPS and sends each visitor to the right program | web, API |
| **web** | All the pages people see | API |
| **API** | Rules, sessions, decisions, tokens, the dashboard's data | database, Valkey, inference |
| **worker** | Background chores: notifying websites, deleting expired data, rotating keys | database, Valkey, the internet (only to notify websites) |
| **inference** | The AI room: looks at frames, returns numbers | **nobody** — it can only receive requests |
| **PostgreSQL** | Long-term memory | — |
| **Valkey** | Short-term memory | — |

!!! key "Key idea — the clean room"
    The inference service is a **clean room**: faces go in, numbers come out. It sits on a private network with **no way out to the internet** and a disk it cannot write to. Even if someone slipped bad code inside, it would have nowhere to send stolen faces and nowhere to store them.

**Trust zones.** We sort every place in the system into zones by how much we trust it:

- the user's device is **untrusted** — everything it says is re-checked;
- the clean room handles faces but keeps nothing;
- the database holds no faces at all;
- the website that asked receives only the sealed letter.

**When things break, the door stays shut.** For every way the system can fail — the AI room crashing, the database going down, a signing key missing — the architecture says exactly what happens. The answer is always *retry* or *try later*, never an accidental *pass*. Engineers call this **failing closed**.

**On the internet:** one rented Linux server runs all the containers with Docker Compose. Caddy faces the internet, and each zone has its own private network. Backups are encrypted every night and stored somewhere else. A Kubernetes version of the same layout is kept ready in case the system ever needs to grow beyond one server.

## 3.9 Stage 5 — The roadmap

The full version, with every deliverable and exit criterion, is `docs/design/05_roadmap.md`.

!!! kid "Explain like I'm six — skateboard first"
    If you need to build a car, don't build four wheels, then a chassis, then an engine, and only find out at the very end whether it drives. Build a **skateboard** first — it already moves you from A to B. Then a scooter, a bicycle, a motorbike, a car. At every step you have something that *works*, and you learn from using it.

    Our skateboard is the **walking skeleton**: a thin version of the *whole* system — shop, verify page, API, AI room (with a pretend model), decision, sealed answer — working end to end before any single part is made fancy.

| Phase | What it delivers |
| :-: | :-- |
| 0 | **Foundations** — the repository, tools, quality checks, automatic testing |
| 1 | **Walking skeleton** — the whole journey working with a stand-in AI model |
| 2 | **The real AI** — datasets, training, the four jars, safety lines, model card |
| 3 | **Catching cheaters** — head-movement and screen-light challenges, real-or-fake model, attack tests |
| 4 | **The platform** — accounts, permissions, keys, policies, notifications, audit trail |
| 5 | **Beautiful front end** — design system, 3D homepage, polished verify flow, dashboard, SDKs |
| 6 | **Stronger checks** — passport/ID reader, then Aadhaar Secure QR |
| 7 | **Hardening** — security scans, monitoring, load tests, privacy documents |
| 8 | **Going live** — the rented server, HTTPS, automatic deploys, backups |
| 9 | **Extras** — reusable "Age Pass", passkeys, and more |

**Definition of Done.** No piece of work counts as finished until it is:

- tidy (formatting and lint checks pass);
- type-checked;
- tested;
- free of secrets or personal data;
- **explained line by line in this book**;
- recorded in an ADR if it was a significant decision;
- green in the automatic checks.

Every phase ends with a written **phase report**: what was built, what was measured, and what changed from the plan, with the reasons.

**Where we are now:** Stages 1–5 are complete. Phase 0 has begun.
