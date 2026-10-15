# Part 1 — The problem

## 1.1 A story

Riya is 14. She has a phone, like most of her friends. One evening a link in a group chat leads to a website showing violent videos that are made for adults. The site has a little box: *"Are you 18 or older? [Yes] [No]"*. Riya taps **Yes**. Nothing stops her.

Nobody did anything illegal by building that box. Until recently, in most countries, that box was considered "enough". That has now changed. Governments around the world have decided that websites with adult content must **actually check** age, not just ask.

This project is about building that check properly — **so that it really works, is fair to everyone, and does not turn into a surveillance machine**.

## 1.2 What is "age-restricted content"?

Anything the law, or a website's own rules, says should only be available above a certain age:

| Kind of content or service | Typical minimum age (varies by country) |
| :-- | :-- |
| Pornography and sexually explicit material | 18 |
| Online gambling and betting | 18 (21 in some US states) |
| Alcohol, tobacco and vape sales | 18 (21 in the US) |
| Graphic violence, self-harm and suicide content | 18 (or "not for children") |
| Social media accounts | 13 in many places; **16 in Australia** since December 2025 |
| Some games and in-app purchases | 12, 16 or 18 depending on rating |
| Processing a child's personal data at all (India) | Under 18 needs a parent's verifiable consent |

!!! key "Key idea"
    The age limit is **not always 18**. That is why Dwarpal treats the age limit as a setting each website chooses (13, 16, 18, 21…), never as a number fixed inside the code.

## 1.3 Why "Are you 18? Yes / No" doesn't work

A **self-declaration** box checks nothing — it trusts the person it is supposed to check. Typing a date of birth is the same thing in a different costume: children simply type an earlier year. Regulators now say this plainly. The UK regulator Ofcom states that self-declaration does **not** count as effective age checking.

So we need something that does not depend on the person telling the truth.

## 1.4 What the law now says — a world tour

!!! kid "Explain like I'm six"
    Different countries have made slightly different rules, but they all say roughly the same thing to websites: **"If you show grown-up stuff, you must really check who is a grown-up — and you must do it fairly, safely, and without being nosy."**

| Where | The rule (simplified) | Since |
| :-- | :-- | :-- |
| 🇬🇧 **United Kingdom** | The *Online Safety Act*. Adult sites and many social platforms need "highly effective age assurance". Ofcom checks four things: **accurate, robust, reliable, fair**. Fines up to £18 million or 10 % of worldwide turnover — and fines are already being issued | July 2025 |
| 🇪🇺 **European Union** | The *Digital Services Act* asks for age checks that are "accurate, reliable, robust, non-intrusive and non-discriminatory". The EU has built an official age-verification app that proves "over 18" **without revealing who you are**; countries are asked to roll it out by the end of 2026 | 2025–2026 |
| 🇺🇸 **United States** | In June 2025 the Supreme Court allowed states to require age verification for adult sites (*Free Speech Coalition v. Paxton*). More than 20 states have such laws. New laws push age checks into app stores and phone operating systems | 2023–2027 |
| 🇦🇺 **Australia** | Children **under 16** may not have accounts on major social media platforms. Platforms must take "reasonable steps"; fines up to AUD 49.5 million | December 2025 |
| 🇮🇳 **India** | The *Digital Personal Data Protection Act* and its 2025 Rules. A "child" is anyone **under 18**, and processing a child's data needs a parent's **verifiable consent**. No tracking, profiling or targeted ads aimed at children. Phased in, with full compliance expected around 2027 | 2025–2027 |

!!! real "Real world"
    In its first six months (July–December 2025), the UK system processed around **69 million age checks across 32 large services**. The two most common methods were **face-based age estimation** and **photo-ID matching**. This is not a classroom problem — it is happening at enormous scale right now.

## 1.5 Three ways to know someone's age

!!! kid "Explain like I'm six — three ways a shopkeeper can know your age"
    1. **Verify:** you show your birth certificate or ID card. The shopkeeper reads your birth date. (Very sure — but you have shown your name, address and photo too.)
    2. **Estimate:** the shopkeeper just *looks* at you and guesses. (Quick and private — but sometimes wrong.)
    3. **Infer:** the shopkeeper notices clues — you drove here yourself, you are paying with a credit card. (Indirect.)

| Method | Official name | Strength | Weakness |
| :-- | :-- | :-- | :-- |
| ID card, passport, bank, digital ID app | **Age verification** | Exact date of birth | Reveals identity; not everyone has ID; documents can be faked or borrowed |
| Looking at the face (or voice, or hand) | **Age estimation** | Fast, no documents, can reveal nothing but "over/under" | It's a guess; it can be wrong, especially close to the limit |
| Other facts (credit card, account history, email history) | **Age inference** | Invisible to the user | Indirect; needs extra data about the person |

All three together are called **age assurance**. Dwarpal uses **estimation first** (fast and private). It falls back to **verification** only when the estimate is too close to call.

## 1.6 How can a computer guess age from a face?

Faces change with age in ways we all recognise: proportions change as children grow, skin texture changes, bone structure matures, and later come wrinkles and grey hair. An **AI model** learns these patterns by looking at hundreds of thousands of face photos whose real ages are known — the same way you learn to guess ages by meeting many people. Part 2 explains exactly how that learning works.

!!! honest "Honest limitation"
    Faces don't come with birth certificates. Some 16-year-olds look 20; some 20-year-olds look 16. Make-up, beards, lighting, camera quality, health and family genes all change how old someone *looks*. Even humans are often wrong by several years. **No AI can remove this uncertainty completely.** A good system doesn't pretend otherwise — it measures its uncertainty and acts carefully when it is unsure.

## 1.7 The two kinds of mistakes

Whenever a guard decides "allowed" or "not allowed", there are two ways to be wrong:

| | Guard says "grown-up, come in" | Guard says "not sure / no" |
| :-- | :-- | :-- |
| **Really a child** | ❌ **Dangerous mistake** — a child gets in | ✅ correct |
| **Really a grown-up** | ✅ correct | ⚠️ **Annoying mistake** — an adult is held up |

!!! kid "Explain like I'm six — the swimming pool"
    A swimming pool has a deep end only for strong swimmers. The lifeguard can make two mistakes: letting in a child who can't swim (**dangerous!**), or stopping a good swimmer (**annoying**, but nobody gets hurt). A sensible lifeguard is **stricter** about the dangerous mistake, and gives the stopped swimmer a fair way to prove themselves — "swim one length for me".

These two mistakes are **not equally bad**. Our whole design is built around that fact:

- We **measure** the dangerous mistake carefully, separately for every age (13, 14, 15, 16, 17). We call it the **false-adult rate**.
- We **set a strict limit** on it — for example "at most 2 in every 100 children near the age limit may get through" — and *calculate* the guard's settings to respect that limit. (The exact method is in Part 3.)
- We give adults who were held up a fair **second route** (another method), instead of just saying "no".

!!! real "Real world — why this matters so much"
    A February 2026 research benchmark tested 34 freely available AI age-guessing models. **Most of the specialised ones called 39–100 % of children "adults"** when the limit was 18. Even huge general-purpose AI models made that mistake 16–29 % of the time. The best commercial systems, measured by the US standards body NIST, let through roughly 5 % of minors when they use a safety margin. So "just download a model" is not safe. The gap between those numbers is what this project's engineering is for.

## 1.8 The safety margin: "Challenge 25"

Shops in the UK selling alcohol follow a rule called **Challenge 25**: the law says 18, but staff ask for ID from anyone who **looks under 25**. The extra seven years are a **buffer**. A 17-year-old might be mistaken for 19, but very rarely for 25.

Age-estimation systems use exactly the same trick, called a **challenge age** or **buffer**. The US National Institute of Standards and Technology (NIST), which tests these systems, measures them this way — for example "accept only if the estimate is 25 or more, for a legal age of 18".

!!! kid "Explain like I'm six — the fairground ride"
    A ride says "you must be 120 cm tall". The measuring stick is wobbly. So the operator says: *if the stick shows 130 cm or more, go straight in. If it shows less, let's measure you properly with the good tape.* The extra 10 cm protects against the wobbly stick.

## 1.9 When the guard isn't sure: "step-up"

What happens to a 20-year-old who looks 19? With a buffer of 25, the guess "19" is not enough to let them in. But we also can't be sure they are a child. So the answer is neither "yes" nor "no", but:

> **"I'm not sure. Please use another method."**

This is called **step-up**: moving to a stronger check, such as an ID document or a digital ID app. Australia's government trial called this a **waterfall**: try the quick, private method first; flow down to a stronger method only when needed.

Dwarpal therefore has **three main answers**, not two: **pass**, **fail**, and **step-up**. (Plus **retry** when the picture was too dark or blurry, and **reject** when it looks like someone is cheating.)

## 1.10 Cheaters: how people try to fool the guard

If there's a gate, someone will try to sneak past. The cheating tricks have names:

| Trick | Example | Official name |
| :-- | :-- | :-- |
| Hold up a photo of an adult | Printed photo, or a photo on another phone | **Presentation attack** (print / screen) |
| Play a video of an adult | A recorded video on a tablet | **Replay attack** |
| Use a fake face | A mask; heavy make-up; a fake beard | **Presentation attack** (mask / disguise) |
| Use a computer-generated face | A video-game character, a 3D avatar, a deepfake | **Presentation / injection attack** |
| Skip the camera completely | Software that pretends to be a camera and feeds in a fake video | **Injection attack** |
| Ask a grown-up to do it | An older sibling or parent looks at the camera | **Proxy** |
| Try again and again | Different lights and angles until it says yes | **Trial-and-error** |

!!! real "Real world — the video-game trick, July 2025"
    Days after the UK's new rules started in July 2025, people discovered that **Discord's face-based age check could be passed with a video-game character**. The game *Death Stranding* has a "photo mode" that lets you move a very realistic character's face. Its controls could even open and close the mouth, which was exactly what Discord's "liveness" step asked for. Reports say characters from other games worked too.

    **Lesson for us:** a simple, predictable "liveness" test (blink, open your mouth) is not enough any more. Part 3 describes our layered defence: **random** head-movement instructions that can't be prepared in advance, and a **screen-light** check — the screen glows in a secret random sequence of colours, and a real face reflects that light in a way a pre-made video or a game character cannot know ahead of time.

!!! honest "Honest limitation"
    No age check can stop a willing adult from doing the check *for* a child (a "proxy"). Regulators accept this. What we can do is make sure **a real, live person was present at the moment of the check**, keep the result short-lived, and tie it to the specific website visit.

## 1.11 Privacy: "look, decide, forget"

Faces are **biometric data** — information about your body. If a company kept millions of children's face photos, a single data leak would be a disaster.

!!! key "Key idea — Dwarpal's privacy promise"
    1. **Look:** the camera frames are used only to make the decision.
    2. **Decide:** the system produces "pass", "fail" or "step-up".
    3. **Forget:** the frames are erased from memory within about a second. They are **never** written to a disk, a log file or a database. There is literally no place in the system where a face could be saved.
    4. **Say as little as possible:** the website learns only "over 18: yes" (or no). Not the guessed age. Not a name. Not anything that could link the same person across different websites.

There is a saying in security: *you can't leak what you never kept.*

## 1.12 Fairness: the same rules for every face

AI models learn from examples. If the examples contain mostly one kind of face — say, light-skinned adult film stars — the model will be worse at guessing other faces. Research, including NIST's testing and Australia's trial, has found exactly this: some systems make more mistakes for some skin tones, for women, or for certain age groups.

An unfair age check is dangerous in **both** directions:

- it can let more children through for some groups (unsafe);
- it can block more adults from some groups (discriminatory).

Dwarpal will **measure** its mistakes separately for different groups, using research datasets that carry those labels. It will refuse to release a model whose groups differ too much. And it will **never** try to guess a person's skin colour or sex during a real check — those labels are only used offline, to test the model.

## 1.13 What our system must do — in plain words

1. Let any website ask: *"Is this live person over N years old?"*
2. Give the person a quick (under 15 seconds), clear, kind experience on any phone or computer.
3. Make a careful guess, **with a measured level of confidence**, and be extra careful near the age limit.
4. Detect cheating: photos, videos, masks, computer-generated faces, fake cameras, repeated tries.
5. Answer **pass**, **fail**, **step-up**, **retry** or **reject** — and when something goes wrong inside the system, **never** answer "pass" by accident. This is called **failing closed**.
6. Send the website a **digitally signed** answer that cannot be forged, containing as little information as possible.
7. **Never keep faces.**
8. Measure and publish how often it makes each kind of mistake, for each age and each group.
9. Give website owners a dashboard: their settings, their keys, their statistics — never anyone's face.
10. Be easy for websites to plug in, and easy for us to run, update and repair.

## 1.14 What our system will never do

- **Recognise who you are.** It answers "how old do you look?", never "who are you?".
- **Store your face**, even "to improve the AI".
- **Guess your race or sex** during a check.
- **Promise to be perfect.** It states its error rates openly instead.

## 1.15 How we'll know we succeeded

- The whole system starts on a laptop with one command, and runs on the internet over HTTPS.
- A demo shop accepts or refuses visitors using the real system.
- We publish, for the AI model: how often children near each age limit would get through, how often adults are held up, and how this differs between groups.
- Our own cheating tests (photos, screen videos, game characters, replayed data) are stopped.
- Security scans are clean, and the system stays fast under load.
- **This book explains 100 % of the code**, and the ledger at the end proves it.
