# Part 0 — Absolute basics

This part assumes you know nothing. If you already know what a server, an API and a database are, skim it. Every later part builds on it.

## 0.1 What is a computer?

A computer is a machine that does exactly three things, over and over, billions of times per second:

1. **Takes in** information (input) — key presses, mouse clicks, a camera picture, a message from the internet.
2. **Works on** that information (processing) — adds numbers, compares them, moves them around.
3. **Gives out** a result (output) — pixels on the screen, sound, a message sent back over the internet.

!!! kid "Explain like I'm six"
    A computer is like a very fast, very obedient cook who can't think for themselves. You give the cook ingredients (input), a recipe (the program), and the cook produces a dish (output). The cook will follow the recipe **exactly** — even if the recipe says "add 100 spoons of salt". The cook never asks "are you sure?".

The important parts inside a computer:

| Part | What it does | Everyday comparison |
| :-- | :-- | :-- |
| **CPU** (Central Processing Unit) | Follows instructions, one tiny step at a time, extremely fast | The cook's brain and hands |
| **GPU** (Graphics Processing Unit) | Does thousands of simple maths operations *at the same time*. Built for drawing graphics; perfect for AI | A kitchen with 5,000 helpers who can each only chop, but all chop at once |
| **RAM** (memory) | Holds what the computer is working on *right now*. Fast, but forgets everything when power is off | The kitchen counter — you put things there while cooking |
| **Storage** (SSD / hard disk) | Keeps files permanently, even when power is off | The cupboard |

The computer this project is being built on has an Intel Core i9-14900HX CPU, an NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB of its own memory, and 32 GB of RAM. That GPU matters: it is what will make **training** our AI model (Part 2) take hours instead of weeks.

!!! key "Key idea — everything is numbers"
    Inside a computer, *everything* — text, photos, music, videos, programs — is stored as numbers. The smallest unit is a **bit**: a single 0 or 1 (think of a light switch, off or on). Eight bits make a **byte**, which can hold a number from 0 to 255.

    - 1 kilobyte (KB) ≈ 1,000 bytes — about a paragraph of text
    - 1 megabyte (MB) ≈ 1,000,000 bytes — about one phone photo
    - 1 gigabyte (GB) ≈ 1,000,000,000 bytes — about a film

    A photo is stored as a grid of tiny dots called **pixels**, and each pixel is three numbers: how much **R**ed, **G**reen and **B**lue light it has (each 0–255). A 640 × 480 camera picture is therefore 640 × 480 × 3 = 921,600 numbers. When our AI "looks at a face", it is really doing arithmetic on numbers like these. Part 2 shows exactly how.

## 0.2 Files, folders and paths

A **file** is a named bundle of bytes kept in storage: a photo, a document, a program. A **folder** (also called a **directory**) is a container for files and other folders, so they form a tree.

The **path** of a file is its full address in that tree. On Windows a path looks like this:

```
C:\Users\anubh\Projects\AI_based_minor_protection\docs\zero_to_hero\build.py
```

Read it left to right: drive `C:`, then folder `Users`, inside it folder `anubh`, … and finally the file `build.py`. The part after the last dot, `.py`, is the **extension**. It hints at what kind of file it is (`.py` = Python program, `.html` = web page, `.md` = Markdown text, `.json` = data, `.jpg` = photo).

!!! warn "Careful — two kinds of slashes"
    Windows separates folders with a **backslash** `\`. Linux and macOS — and web addresses — use a **forward slash** `/`. Our code must run on both (development on Windows, servers on Linux), so it uses tools that handle either. In this book we usually write paths with `/`, like `docs/zero_to_hero/build.py`. That kind of path, measured from the project's main folder, is called a **relative path**.

### Text files and encodings

Some files contain **text** (letters you can read); others contain **binary** data (photos, programs). But text is numbers too: each letter needs a number. The agreement that says "the number 65 means *A*" is called a **character encoding**.

The modern encoding is **UTF-8**. It can store every character in every language — English, हिन्दी, emoji 🧒 — and it is what every file in this project uses.

!!! real "Real world — what goes wrong when encodings disagree"
    If a program *writes* a file in UTF-8 but another program *reads* it assuming an older encoding (such as Windows-1252), characters turn into garbage called **mojibake**. A long dash "—" becomes "â€”". This exact bug appears in the HTML documentation of a previous project by the same team. That is why the builder of this book reads and writes every file as UTF-8 **explicitly** — you will see the exact line in Part X.

## 0.3 What is a program?

A **program** is a file (or many files) of instructions for the computer. The instructions are written by people, in a **programming language**, as plain text. That text is called **source code**, or just **code**.

!!! kid "Explain like I'm six"
    A program is a recipe. A recipe for tea might say:

    1. Fill the kettle with water.
    2. Switch it on.
    3. **If** you want it sweet, add sugar.
    4. **Repeat** stirring 5 times.

    Programs have exactly these ingredients: **steps** in order, **decisions** ("if …"), and **repetition** ("repeat …"). Everything else is detail.

Programs are *precise*. A human understands "add some sugar"; a computer needs "add 2 spoons". Most of programming is turning a fuzzy human wish into precise steps — and most bugs come from a step that wasn't quite what the programmer meant.

## 0.4 Programming languages

Computers really only understand **machine code**: long lists of numbers that mean things like "add these two" or "jump to step 7". Humans can't comfortably write that, so we write in **programming languages** that read almost like English. Other programs then translate them for the computer.

| Language | Used in this project for | What it looks like |
| :-- | :-- | :-- |
| **Python** | The servers (backend), the AI, the tools (including the one that builds this book) | `if age >= 18: print("welcome")` |
| **TypeScript** | The websites people see (frontend). It is JavaScript with extra safety checks called *types* | `if (age >= 18) { show("welcome") }` |
| **JavaScript** | What web browsers actually run. TypeScript is converted into it | same as above, minus the types |
| **HTML** | Not a programming language — a *markup* language that describes what's on a web page | `<h1>Welcome</h1>` |
| **CSS** | A *style* language: colours, sizes, layouts | `h1 { color: blue; }` |
| **SQL** | The language for asking a database questions | `SELECT * FROM sessions WHERE outcome = 'pass'` |

There are two broad ways a language gets run:

- **Interpreted** (Python, JavaScript): another program — the **interpreter** — reads your code and does what it says, line by line, while it runs.
- **Compiled** (C, Rust, Go): a **compiler** translates the whole program into machine code *first*, producing a file that runs directly.

!!! why "Why Python for the backend and the AI?"
    Nearly every modern AI tool (PyTorch, ONNX Runtime, OpenCV, MediaPipe) is built for Python first. Using Python for both the AI *and* the servers means one language for the whole back half of the system — and one language for you to learn. The speed cost of an interpreted language barely matters here, because the slow part (the AI maths) runs inside highly optimised libraries written in faster languages.

## 0.5 The terminal

Before mouse-and-window interfaces, people used computers by typing commands. That way of working still exists and programmers use it constantly. The window you type commands into is called a **terminal** (on Windows: **PowerShell** or **Command Prompt**). The program that reads your commands is called a **shell**.

!!! try "Try it yourself"
    Open PowerShell (press the Windows key, type *PowerShell*, press Enter) and type:

    `python --version`

    and press Enter. The computer answers with something like `Python 3.14.6`. You just asked a program a question and got an answer — that is what every command does.

Throughout this book, commands you can type are shown in boxes like this:

```bash
python build.py
```

## 0.6 How computers talk: networks and the internet

A **network** is computers connected so they can send each other messages. The **internet** is the network of all networks — billions of devices.

Messages travel in small chunks called **packets**. To deliver a packet, the network needs an address:

- An **IP address** is a computer's address on a network, like a house address. It looks like `142.250.183.14` (IPv4) or a longer form with colons (IPv6).
- A **port** is a numbered door on that computer (0–65535). One computer can run many programs that talk to the network; each listens behind its own door. Web traffic usually uses door **443** (secure) or **80** (old, insecure).

!!! kid "Explain like I'm six"
    The IP address gets the letter to the right **building**. The port number gets it to the right **flat** inside the building. Every program that wants to receive letters must sit behind a flat door with a number on it.

- **`localhost`** (or `127.0.0.1`) is a special address that always means "this same computer". When we run the project on our own laptop, we visit addresses like `http://localhost:3000`.
- **DNS** (Domain Name System) is the internet's phone book. Humans remember names like `google.com`; DNS translates them into IP addresses. When we put Dwarpal on the internet, we'll buy a name and add a DNS record pointing it at our server's IP address.

## 0.7 Clients and servers

Most internet programs come in pairs:

- A **client** *asks* for something. Your web browser is a client.
- A **server** *answers*. It is a program that starts up and then waits — forever — for clients to ask it things. Waiting for messages on a port is called **listening**.

!!! kid "Explain like I'm six — the restaurant"
    You sit at a table and order (you are the **client**). The waiter takes your order to the kitchen (the **server** — it waits all day for orders). The kitchen prepares the dish and sends it back. You never go into the kitchen, and the kitchen never comes to your house. The menu tells you what you're allowed to order.

The word "server" means two things — the *program* that answers and the *computer* it runs on. When people say "the website is on a server", they mean a computer, usually in a data centre, running server programs 24 hours a day.

Dwarpal has several servers. Each is a program with its own job, and each listens on its own port:

| Server | Its job | Language |
| :-- | :-- | :-- |
| **Web app** | Sends the pages you see in your browser | TypeScript (Next.js) |
| **API** | The "brain office": sessions, rules, decisions, signed answers | Python (FastAPI) |
| **Inference service** | The "AI room": looks at the frames and does the maths | Python + ONNX Runtime |
| **Database** | Remembers things long-term | PostgreSQL |
| **Valkey** | Remembers things short-term, very fast | Valkey |

## 0.8 HTTP — the language of the web

When a client and a server talk, they need an agreed **protocol**: rules for how messages are formatted. The web's protocol is **HTTP** (HyperText Transfer Protocol).

Every HTTP conversation is one **request** followed by one **response**.

**A request has:**

- a **method** — what kind of action is wanted;
- a **path** — which thing it's about;
- **headers** — extra labels, like the envelope of a letter;
- (sometimes) a **body** — the contents, like the letter inside.

```
POST /v1/verification-sessions HTTP/1.1
Host: api.dwarpal.example
Authorization: Bearer dk_test_EXAMPLEKEY000000000000
Content-Type: application/json

{"policy": "uk_osa_18_standard", "return_url": "https://shop.example/age-ok"}
```

**The common methods:**

| Method | Means | Example in Dwarpal |
| :-- | :-- | :-- |
| `GET` | "Give me this" (never changes anything) | Get the result of a verification session |
| `POST` | "Create something / do something" | Create a new verification session |
| `PUT` / `PATCH` | "Replace / update this" | Change a policy |
| `DELETE` | "Remove this" | Revoke an API key |

**A response has** a **status code** (a three-digit number that summarises what happened), headers, and usually a body:

```
HTTP/1.1 201 Created
Content-Type: application/json

{"id": "vs_01JA8...", "url": "https://verify.dwarpal.example/s/vs_01JA8...", "status": "pending"}
```

| Code | Name | Means |
| :-- | :-- | :-- |
| 200 | OK | Here's what you asked for |
| 201 | Created | I made the thing you asked me to make |
| 204 | No Content | Done; nothing to send back |
| 301 / 302 | Moved | Look over there instead |
| 400 | Bad Request | Your request doesn't make sense |
| 401 | Unauthorized | I don't know who you are (missing or wrong key) |
| 403 | Forbidden | I know who you are, but you're not allowed |
| 404 | Not Found | That doesn't exist |
| 409 | Conflict | That clashes with something that already happened |
| 422 | Unprocessable | I understood the format, but the values are invalid |
| 429 | Too Many Requests | Slow down — you're over your limit |
| 500 | Internal Server Error | Something broke on my side |
| 503 | Service Unavailable | I can't answer right now, try later |

!!! key "Key idea"
    The first digit tells you who is responsible: **2xx** = success, **3xx** = go elsewhere, **4xx** = the *client* made a mistake, **5xx** = the *server* made a mistake. Dwarpal follows these rules carefully, because the websites that use it will write code that reacts to these numbers.

## 0.9 HTTPS — the padlock

Plain HTTP travels like a postcard: anyone the message passes through can read it. **HTTPS** is HTTP inside a sealed, tamper-proof envelope. The sealing technology is called **TLS** (Transport Layer Security). The padlock icon in your browser means "this conversation is sealed".

The server proves its identity with a **certificate**: a digital document, signed by a trusted organisation, saying "this server really is `dwarpal.example`".

!!! key "Key idea — why HTTPS isn't optional for us"
    Browsers **refuse to give a web page access to your camera unless the page is served over HTTPS** (or from `localhost` during development). This is a deliberate browser security rule. Our whole system depends on the camera, so HTTPS is built in from day one. We'll use a program called **Caddy** that gets and renews certificates automatically.

## 0.10 How a web page is made: HTML, CSS and JavaScript

When you open a website, your browser asks a server for files and turns them into the page you see. There are three kinds:

!!! kid "Explain like I'm six — building a puppet"
    - **HTML** is the puppet's **skeleton**: what parts exist (a heading here, a button there, a picture below).
    - **CSS** is the puppet's **clothes and paint**: colours, sizes, where things sit.
    - **JavaScript** is the puppet's **muscles**: it makes things move and react when you click, type or look at the camera.

```html
<h1>Are you old enough?</h1>
<button id="start">Start age check</button>
```

```css
h1 { font-size: 32px; color: #0969da; }
```

```javascript
document.getElementById("start").addEventListener("click", startCamera);
```

The **frontend** is everything that runs in the user's browser. The **backend** is everything that runs on our servers. Users never see the backend directly; they only see what the frontend shows them.

## 0.11 APIs and JSON

An **API** (Application Programming Interface) is a menu of requests that one program offers to other programs. A website shows *buttons* to humans. An API offers *endpoints* — specific paths and methods — to other programs. For example, `POST /v1/verification-sessions` is one endpoint on Dwarpal's API.

When programs exchange data, they need a shared format. The most common is **JSON** (JavaScript Object Notation). It is plain text with just six kinds of value:

| Kind | Looks like | Means |
| :-- | :-- | :-- |
| String | `"hello"` | Text, always in double quotes |
| Number | `42`, `0.97` | A number |
| Boolean | `true` / `false` | Yes or no |
| Null | `null` | "Nothing here" |
| Array | `[1, 2, 3]` | An ordered list |
| Object | `{"age_over": 18}` | Labelled values ("key": value) |

```json
{
  "id": "vs_01JA8XQ2",
  "outcome": "pass",
  "age_over": 18,
  "methods": ["face_estimation", "liveness_active"]
}
```

That is everything — all JSON is these six kinds nested inside each other.

## 0.12 Databases

Programs forget everything when they stop, like the kitchen counter being wiped clean every night. A **database** is a program that **remembers**, safely and permanently, and can quickly answer questions about what it remembers.

The most common kind is a **relational database**. It stores data in **tables**, a bit like spreadsheets:

| id | policy | outcome | created_at |
| :-- | :-- | :-- | :-- |
| vs_01JA8XQ2 | uk_osa_18_standard | pass | 2026-10-15 10:02 |
| vs_01JA8XR7 | uk_osa_18_standard | step_up | 2026-10-15 10:03 |

Each row is one thing (here, one verification session). Each column is one property of it. You talk to it in **SQL**:

```sql
SELECT outcome, COUNT(*) FROM verification_sessions GROUP BY outcome;
```

That asks: "for each outcome, how many sessions had it?"

!!! why "Why a real database instead of saving files?"
    Two people can't safely write to the same file at the same moment. A database handles thousands of simultaneous readers and writers without corrupting anything. It guarantees that a group of changes either *all* happen or *none* happen — this is called a **transaction**. It also enforces rules ("every session must belong to a project"). Dwarpal uses **PostgreSQL**, one of the most trusted databases in the world.

## 0.13 Where websites live: hosting, the cloud and domains

To be reachable by everyone, our servers must run on a computer that is **always on and connected to the internet**. Your laptop sleeps and moves around, so instead we **rent** a computer in a data centre.

- **Hosting** = renting space and computing power to run your website.
- **The cloud** = companies (Amazon Web Services, Google Cloud, Microsoft Azure, Hetzner, Oracle Cloud, …) that rent out computers by the hour or month.
- A **VM** (virtual machine) or **VPS** (virtual private server) = a slice of a big computer that behaves like your own private computer.
- **Deploying** = copying your program onto that rented computer and starting it.
- A **domain** = the human-friendly name (like `dwarpal.example`) that you rent from a registrar, then point at your server with DNS.

!!! kid "Explain like I'm six"
    Your laptop is your home kitchen. Hosting is renting a stall in a big food market that never closes. The domain name is the sign above your stall, so people can find it. Deploying is carrying your recipes and ingredients to the stall and starting to cook there.

## 0.14 Containers and Docker

Software that works perfectly on your laptop often breaks on a server: a different operating system, a missing library, a different version of Python. **Docker** solves this by packing a program **together with everything it needs** into one sealed box.

| Word | Meaning | Lunchbox comparison |
| :-- | :-- | :-- |
| **Image** | The sealed, read-only package: the operating system bits, the language version, the libraries, your code | A packed lunchbox recipe — the same every time |
| **Container** | A running copy of an image | An actual lunchbox, opened and being eaten |
| **Volume** | A folder that survives when the container is thrown away | A thermos you keep and refill |
| **Docker Compose** | A file that describes several containers that work together, and starts them all with one command | A picnic plan: "three lunchboxes, two thermoses, start them together" |

Dwarpal will start completely — web app, API, AI service, database, everything — with **one command**:

```bash
docker compose up
```

## 0.15 Git — a time machine for code

**Git** is a tool that records the history of a project.

- Every time you reach a good point, you make a **commit**: a snapshot of all files plus a message saying what changed and why.
- You can go back to any earlier snapshot, compare two snapshots, or work on an experiment in a separate **branch** without disturbing the main version.
- **GitHub** is a website that stores Git projects online, so teams can share them and computers can automatically test every change.

!!! kid "Explain like I'm six"
    Git is a "save game" button for code. Every save has a name and a note. If you break something, you load the last good save.

## 0.16 Open source and licences — why "free to download" isn't "free to use"

A huge amount of software (and many AI models and datasets) is **open source**: the code is published for anyone to read. But publishing is not the same as permission. Every project comes with a **licence** — the legal rules for what you may do with it.

| Licence family | Examples | What it allows | Effect on us |
| :-- | :-- | :-- | :-- |
| **Permissive** | MIT, Apache-2.0, BSD | Use it for anything, including selling, as long as you keep the copyright notice | ✅ We prefer these |
| **Copyleft** | GPL, **AGPL** | Use it, but if you distribute it (AGPL: or even just offer it over a network), you must publish *your* code under the same licence | ⚠️ Avoided in the running system |
| **Non-commercial** | CC BY-NC, "research only" | Use it only for research or education — never to make money | ⚠️ Fine for this academic project, but blocks commercial use |

!!! real "Real world — licences shaped this project's design"
    - The popular **YOLOv8** face detector is **AGPL**, so we chose **YuNet** (MIT licence) instead.
    - Many well-known **face datasets** used to train age models (IMDB-WIKI, UTKFace, …) are **research-only**. Our AI model can be trained on them for this project, but a company selling Dwarpal would have to retrain on properly licensed data.

    That is why the system treats the AI model as a **replaceable part** with a version number, not as something welded in. Part 3 explains this decision.

## 0.17 Libraries, packages and versions

Nobody writes everything from scratch. A **library** (or **package**) is code someone else wrote and shared, so you can use it. Examples: a library that reads photos, a library that does the AI maths, a library that turns Markdown into HTML.

- A **package manager** downloads libraries for you: **pip** or **uv** for Python, **npm** or **pnpm** for JavaScript.
- Libraries have **version numbers** such as `3.11.1`. These are usually *major.minor.patch*: a bigger last number means a small bug fix, a bigger middle number means new features, and a bigger first number may mean breaking changes.
- **Pinning** means writing down the *exact* version you tested with (like `markdown==3.11.1`). Then the project builds the same way next month, on another computer, or on a server.
- A **lockfile** (`uv.lock`, `pnpm-lock.yaml`) is an automatically generated list of the exact versions of *every* library, including the libraries your libraries use.

!!! warn "Careful"
    "It worked yesterday" bugs very often come from a library quietly updating itself. Pinning versions prevents that. Every library in Dwarpal is pinned.

## 0.18 Putting it all together — the journey of one age check

Here is everything from Part 0 in one story. Later parts explain each step in depth.

1. Asha, 26, visits a (fictional) online shop that sells wine. Her **browser** (a **client**) asks the shop's **server** for a page using **HTTPS**.
2. The shop must check her age. Its server sends a **POST** request to Dwarpal's **API**, authenticated with the shop's secret **API key**. Dwarpal's API saves a new session in the **database** and replies with **JSON** containing a link.
3. Asha's browser opens Dwarpal's verification page (**HTML**, **CSS**, **JavaScript**). With her permission — only possible because the page uses **HTTPS** — it turns on the camera.
4. JavaScript running in her browser helps her line up her face. Then it sends a few camera **frames** (photos, which are just numbers) to the API.
5. The API passes them to the **inference service**. There, the **AI model** — running on the **CPU** — turns the numbers into an age estimate and a liveness check. The frames are then forgotten.
6. The API's decision engine says **pass**. It creates a digitally **signed** answer and records "pass" (never the face) in the **database**.
7. Asha's browser goes back to the shop. The shop's server checks the signature and lets her buy the wine.

All of this runs inside **Docker containers** on a rented **VM** reachable at a **domain** name. The code is tracked with **Git**, built from **pinned** libraries with suitable **licences**.

If every bold word above now makes at least a little sense, you're ready for Part 1.
