# Part 6 — Launch night: putting Dwarpal on the internet

On the evening of **10 November 2026**, Dwarpal left the laptop and went live at **`https://dwarpal-age.duckdns.org`**. The owner had never used a cloud service or a server before. They clicked through Oracle's console, GitHub's settings, DuckDNS and Google's account pages, one instruction at a time, without knowing what most of the screens were for. This part explains **everything that happened that night, from zero**: every service, every key, every click, and how all of it fits together into one working website.

If you read only one part of this book to understand "how a website gets onto the internet", read this one. Its last sections were added afterwards: the trained age model's move to the server (§6.15), how all the services work together on one visit (§6.16), where every key lives (§6.17), short answers for an interview (§6.18), and the day that move broke the demo shop (§6.19).

!!! kid "Explain like I'm six"
    Imagine you baked a wonderful cake at home (that's Dwarpal on the laptop). Tonight you **rented a shop on a busy street** (Oracle's server), **got a lock and a key for its back door** (SSH keys), **put up a sign with the shop's name** (DuckDNS), had **a bakery factory make sealed boxes of your cake** (GitHub building images), **carried the boxes to the shop and opened it** (the deploy), **hired a guard who checks everyone at the front door** (Caddy and HTTPS), **asked a friend to phone you if anything breaks** (alert emails) and **put a copy of the recipe book in a bank locker every night** (backups). Each section below is one of those steps.

## 6.1 The whole picture on one page

Before the details, here is the finished thing. Every arrow is a real connection that exists now.

```text
                        YOUR LAPTOP (Windows)
   ~/.ssh/dwarpal  ──── SSH (owner key) ─────────────┐
   ~/.ssh/dwarpal_deploy ─ copied to GitHub as a secret
                                                     │
   GITHUB (github.com/Anubhav104401/Dwarpal)         │
   - the code                                        │
   - Actions: builds 4 images on Arm machines ──► GHCR (ghcr.io: the image shelf)
   - deploy job ── SSH (deploy key) ────────────────►│
                                                     ▼
   ORACLE CLOUD, Hyderabad ── one rented computer ("instance" dwarpal), Ubuntu 24.04, 2 cores, 12 GB
   ┌──────────────────────────────────────────────────────────────────────────────────────┐
   │ firewall: only 22 (SSH), 80 (HTTP), 443 (HTTPS) may come in                           │
   │ Docker runs 12 containers:                                                            │
   │   caddy ──► web (home page, console, verify page)   ◄── dwarpal-age.duckdns.org       │
   │         ──► api (the API websites call)             ◄── api.dwarpal-age.duckdns.org   │
   │         ──► shop (Amber Cellars, the demo)          ◄── shop.dwarpal-age.duckdns.org  │
   │   inference (the AI)  postgres (database)  valkey (short-term memory)                 │
   │   webhooks  maintenance  collector  prometheus  alertmanager ──► Gmail ──► you        │
   │ /opt/dwarpal: compose.yaml, Caddyfile, .env (secrets), models/                        │
   │ every night 02:00 IST: backup.sh ──► encrypted ──► Oracle Object Storage bucket       │
   └──────────────────────────────────────────────────────────────────────────────────────┘
                                                     ▲
   DUCKDNS: "dwarpal-age.duckdns.org → 140.245.234.110"  (the phone book entry)
   LET'S ENCRYPT: gave Caddy the HTTPS certificate (the padlock)
   GITHUB ACTIONS "uptime": checks the site from outside every 15 minutes
```

| Company / thing | What it gave us | Cost |
| :-- | :-- | :-- |
| **Oracle Cloud** | The computer the site runs on, its network, its public address, and storage for backups | ₹0 inside the Always Free limits (see §6.2 about the card charge) |
| **DuckDNS** | A free name, `dwarpal-age.duckdns.org`, pointing at that computer | Free (volunteer-run) |
| **GitHub** | Keeps the code; its **Actions** robots build the images and deploy them; **GHCR** stores the images | Free for a public repository |
| **Let's Encrypt** | The HTTPS certificate (the padlock) | Free |
| **Gmail** | Sends the alert emails | Free |
| **Your laptop** | Holds the two SSH keys, and the code | — |

## 6.2 Oracle Cloud: renting a computer

### What a "cloud" company sells

A cloud company owns huge buildings (**data centres**) full of computers. It **rents** pieces of them to anyone, by the hour. Oracle, Amazon (AWS), Google and Microsoft (Azure) are the big ones. Renting is cheaper and easier than buying a computer, keeping it switched on 24 hours a day, cooling it and connecting it to a fast internet line yourself.

**Their business model** is simple: you pay for what you use (each hour of computer time, each gigabyte stored, each gigabyte sent out). To win new customers, Oracle gives an **Always Free** amount that never expires: Arm computers with 2 cores and 12 GB of memory in all (4 and 24 GB on an upgraded account, §5.8.1), 200 GB of disk, and 20 GB of Object Storage. They hope that people who learn on the free amount will later run big, paid systems there. Dwarpal fits inside the free amount.

!!! key "Key idea — a credit card is asked for even on free accounts"
    Free computers attract abusers (spam, crypto-mining, attacks). To make that harder, Oracle checks a real card. When signing up, it took a small amount and returned it within seconds. When the account was upgraded to **Pay As You Go** that night, it took **100 US dollars** as a *verification amount*. Oracle's own documentation calls this an authorisation that it reverses, but on the owner's debit card it showed as a completed debit, and a refund request was opened with Oracle Support. **Lesson recorded for the future:** before any step that touches a card, state the exact amount and how it is returned, before clicking.

### Why we upgraded: "Out of capacity"

Oracle's free Arm machines are so popular that the Hyderabad data centre often has none left for free accounts. Creating the server failed with **"Out of capacity for shape VM.Standard.A1.Flex"**, and after many retries with **"Too many requests"**. Pay As You Go accounts are served first, so the account was upgraded. It still pays **₹0** as long as it stays inside the Always Free amounts; a **budget alert** emails the owner if any cost ever appears.

### The words on Oracle's screens

| Word on the screen | What it means | Ours |
| :-- | :-- | :-- |
| **Tenancy** | Your whole Oracle account, like a company's account at a bank | the name chosen at sign-up |
| **Region** | Which city's data centre | India South (Hyderabad), `ap-hyderabad-1`: close to Indian users, so pages load fast |
| **Availability domain (AD)** | A separate building within a region, with its own power. Hyderabad has only one | AD-1 |
| **Compartment** | A folder to group your cloud things | the root compartment |
| **VCN** (virtual cloud network) | Your own private network inside Oracle, like the wiring inside a house | `dwarpal-vcn` |
| **Subnet** | A part of that network. A *public* subnet's computers can have internet addresses | `public subnet-dwarpal-vcn`, addresses `10.0.0.x` |
| **Internet gateway** | The front door between your network and the internet. The "VCN with Internet Connectivity" wizard made it | made by the wizard |
| **Security list** | Oracle's outer firewall: which kinds of traffic may enter the subnet | port 22 (SSH), 80 (HTTP), 443 (HTTPS) |
| **Instance** | One rented computer | `dwarpal` |
| **Image** (on Oracle) | The operating system the computer starts with, copied onto its disk | Canonical Ubuntu 24.04 for Arm |
| **Shape** | The size of the computer | `VM.Standard.A1.Flex` with 2 **OCPUs** (cores) and 12 GB of memory |
| **Ampere / A1 / Arm** | The kind of processor: Arm chips, like a phone's, not Intel/AMD ("x86") | Arm, so every image is built for Arm |
| **Public IP address** | The computer's number on the internet | `140.245.234.110` |
| **Boot volume** | Its disk | 47 GB |
| **Object Storage / bucket** | A different product: a huge, cheap cupboard for files, reached over the internet | bucket `dwarpal-backups` |
| **Namespace** | Your tenancy's short, random name in Object Storage addresses | a short random string |

!!! warn "Careful — the word *image* means two different things tonight"
    On **Oracle's** screen, an *image* is a whole **operating system** (Ubuntu) copied onto the computer's disk when it is created. In **Docker** (§0.14 and §6.6), an *image* is a sealed package of **one program** with everything it needs. Our Oracle computer started from the Ubuntu image, and then ran twelve Docker containers made from ten different Docker images: Dwarpal's own four, plus Caddy, PostgreSQL, Valkey and the three of the alarm system.

### Two things that went wrong while creating it

1. **"Incorrectly formatted request".** The plan was to paste `infra/vm/cloud-init.yaml` (§5.8.1) into the *Initialization script* box, so the server would prepare itself on its first boot. Oracle refused the form with this error, and it only went through with the box empty. So the same steps were run **over SSH** right after the server started (§6.4). The result is the same.
2. **The public-address switch was grey** when the network was created inside the instance form. Making the network first with Oracle's *VCN with Internet Connectivity* wizard, then choosing it in the form, fixed it.

## 6.3 SSH and keys: the secret handshake

### What SSH is

**SSH** (Secure Shell) lets you type commands on a computer far away as if you were sitting at it. Everything sent is encrypted. It is how almost every server in the world is looked after. When you see

```bash
ssh -i ~/.ssh/dwarpal ubuntu@140.245.234.110
```

read it as: "using the key in the file `~/.ssh/dwarpal`, log in as the user `ubuntu` on the computer at `140.245.234.110`". (`~` means your home folder; on this laptop that is `C:\Users\anubh`.) Its cousin **`scp`** (secure copy) copies files over the same kind of connection: that is how the deploy files and the AI models reached the server.

### What an SSH key is: a padlock and its only key

Passwords can be guessed. So instead, SSH uses a **key pair**, made of two matching halves:

| Half | File on the laptop | Who may see it | What it does |
| :-- | :-- | :-- | :-- |
| **Private key** | `C:\Users\anubh\.ssh\dwarpal` | **Nobody.** Never send it, never paste it in a chat or a repository | Proves "I am the owner" by *signing* a challenge |
| **Public key** | `C:\Users\anubh\.ssh\dwarpal.pub` | Anyone; it is safe to share | Checks those signatures. It was pasted into Oracle's form, and Oracle wrote it on the new server, in `/home/ubuntu/.ssh/authorized_keys` |

When you connect, the server sends a random challenge. Your laptop **signs** it with the private key. The server checks the signature with the public key it holds. Only the real private key can make a signature that checks, and the private key itself **never travels**.

!!! kid "Explain like I'm six"
    You gave the shop a **padlock** that only your key opens (the public key), and you kept **the key** in your pocket (the private key). Anyone can look at the padlock; it doesn't help them open it. Lose the key, though, and whoever finds it can walk in. So the key stays in your pocket.

### Where the keys came from

The command was:

```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\dwarpal -C owner
```

- **`ssh-keygen`** is part of the OpenSSH program that **Windows already includes** (it has shipped with Windows 10 and 11 since 2018). Nothing was downloaded.
- **`-t ed25519`** picks the kind of key: **Ed25519**, a modern, fast and very secure maths method (an elliptic curve). Its public key is just 32 bytes.
- **The randomness** comes from Windows' built-in **cryptographic random number generator**, which mixes in unpredictable events from the hardware (tiny timing differences, processor noise). That is what makes your private key impossible to guess: there are about 2²⁵² possible keys, more than the number of atoms in the Earth.
- **`-f $HOME\.ssh\dwarpal`** is where to save it. The first try with `~/.ssh/dwarpal` failed: Windows PowerShell doesn't understand `~` in this place, and the `.ssh` folder didn't exist yet. `$HOME` does work.
- **`-C owner`** is just a label written at the end of the public key.
- It asked for a **passphrase**, a password that locks the private key file itself. Leaving it empty means no typing every time, but anyone who copies the file can use it. It was left empty.

**Two keys were made, for two different users:**

| Key | Used by | Why separate |
| :-- | :-- | :-- |
| `dwarpal` | **You** (and the assistant, on your laptop) to log in and look after the server | Your personal key |
| `dwarpal_deploy` | **GitHub's deploy robot** | Its private half is stored inside GitHub (§6.6). If GitHub were ever breached, you remove only this one line from the server, and your own key keeps working |

### The server's key: knowing you reached the real server

It works the other way too. The **server** has its own key pair (its *host key*), so your laptop can tell it is talking to the real server and not an impostor. The first connection saved the server's public host key in **`C:\Users\anubh\.ssh\known_hosts`** ("Permanently added '140.245.234.110' to the list of known hosts"). From then on, a different answer would raise an alarm. GitHub got the same list, as the variable `DEPLOY_KNOWN_HOSTS`, made with `ssh-keyscan`.

## 6.4 Preparing the server

A new Ubuntu computer on the internet is like a new house with the doors unlocked. Within minutes of getting a public address, robots start trying to log in. Before running anything, the steps from `cloud-init.yaml` (§5.8.1) were run over SSH as **`sudo`** ("do this as the administrator"):

| Step | What and why |
| :-- | :-- |
| **SSH by key only** | No passwords at all, no logging in as `root` (the all-powerful user), at most 3 tries per connection. Guessing robots get nowhere |
| **Updates** | `apt` (Ubuntu's app store for programs) installed every security fix, and **unattended-upgrades** now installs new ones every day by itself, restarting the server at 03:00 IST if a fix needs it |
| **Docker and Compose** | The engine that runs the containers (version 29.1) and the tool that starts them all together (§0.14) |
| **Firewall** | Oracle's Ubuntu has a second firewall *inside* the computer (`iptables`) that only let SSH in. Rules were added for **80** and **443** (TCP, and UDP for the fast HTTP/3), above its last "reject everything else" rule, and saved so they survive restarts. So there are **two** walls: Oracle's security list outside, `iptables` inside |
| **Swap** | 4 GB of disk that can act as spare memory, so a brief rush doesn't crash anything |
| **Docker's logs capped** | at 3 files of 10 MB per container, so the disk can't fill with logs |
| **`/opt/dwarpal`** | The folder where Dwarpal lives, readable only by the `ubuntu` user |

!!! key "Key idea — ports are numbered doors"
    One computer runs many services at once. Each listens behind a numbered **port**. 22 is SSH's door, 80 is plain web (HTTP), 443 is encrypted web (HTTPS). A firewall decides which doors are open to the outside. Ours opens exactly three; the database (5432) and everything else are reachable **only** from inside the server.

## 6.5 Files, secrets and models

1. **The deploy files** were copied with `scp` into `/opt/dwarpal`: `compose.yaml` (which containers to run, §5.8.2), `Caddyfile` (which address goes to which container), the scripts, and the alert rules.
2. **The secrets** were *made on the server* by `gen_secrets.py`, and never left it: the database passwords, Valkey's password, the shop's secret, and the **master key** that locks the keys Dwarpal signs its age tokens with. They live in `/opt/dwarpal/.env`, readable by its owner only. Nobody, not even the assistant, ever saw them.
3. **The AI models** (six files, about 25 MB): face finding, face landmarks, hand landmarks, face recognition, and the two **anti-spoofing** networks that spot a photo or a screen held up to the camera. They were copied from the laptop with `scp`. Without the anti-spoofing pair, every live check would be refused, so the first thing checked after the deploy was `"antispoof":"loaded"`. The seventh model, the trained age model, followed two days later (§6.15).

## 6.6 GitHub: the factory that builds and delivers

### Images, built far away

A **Docker image** (§0.14) is one program sealed in a box with everything it needs. Dwarpal has four of its own:

| Image | What's inside |
| :-- | :-- |
| `dwarpal-api` | The API in Python: accounts, projects, keys, sessions, tokens |
| `dwarpal-inference` | The AI service: the face, liveness and age models, and the ID-card reader |
| `dwarpal-web` | The website: home page, console and verify page (Next.js) |
| `dwarpal-demo-shop` | Amber Cellars, the pretend wine shop that shows Dwarpal in use |

The server is an **Arm** computer, and the laptop is not. Building Arm images on the laptop would be slow, and the project decided (D17) that the big base images are only ever downloaded by GitHub and the server. So **GitHub Actions** builds them: when you pressed **Run workflow** on the *deploy* workflow, GitHub lent four of its own Arm computers for a few minutes. Each followed one recipe (a `Dockerfile`), built one image, and put it on **GHCR** (GitHub Container Registry, `ghcr.io`), a shelf for images. The four packages were already **public**, so the server can fetch them without logging in, which was checked from the server (each answered `200`).

### Settings you added on GitHub, and why

| Setting | Kind | What it's for |
| :-- | :-- | :-- |
| `DWARPAL_PUBLIC_API_URL` | Variable | The API's address, baked into the website when it is built, and checked by the *uptime* robot every 15 minutes |
| `DEPLOY_HOST` | Variable | Which computer to deploy to: the server's IP address |
| `DEPLOY_KNOWN_HOSTS` | Variable | The server's public host keys (§6.3), so the robot knows it reached the real server |
| `DEPLOY_SSH_KEY` | **Secret** | The private half of the *deploy* key. GitHub keeps secrets encrypted and never shows them again, not even to you |
| `production` | Environment | A gate: the deploy step waits until **you** press *Approve and deploy* |

### What happened when you pressed Approve

The second half of the workflow, *Deploy — over SSH, health-gated*, logged in to the server with the deploy key and ran `deploy.sh`:

1. It asked the server to **pull** (download) the four new images from GHCR, and the official PostgreSQL, Valkey and Caddy images from Docker Hub.
2. It ran the **migrations**, which create the database's tables (§5.4).
3. It started every container and **waited for each to say "healthy"**. If they hadn't within five minutes, it would have rolled back to the previous version.
4. It asked the AI service whether the anti-spoofing models were loaded.

The very first run had "Also deploy" ticked by mistake. That was harmless: the **production gate** held the deploy step until the images were confirmed public, and then that same run was approved.

## 6.7 DuckDNS and DNS: the internet's phone book

Computers find each other by **numbers** (IP addresses). People remember **names**. **DNS** (the Domain Name System) is the world's phone book that turns one into the other. A free service, **DuckDNS**, gave us the name `dwarpal-age.duckdns.org`. On its page you typed the server's number into *current ip* and pressed *update ip*. The first time, the box showed `101.0.63.248`, **your home internet's** address, which DuckDNS fills in by itself; it had to be replaced with the server's. A minute later, any device in the world asking "where is `api.dwarpal-age.duckdns.org`?" got `140.245.234.110`.

DuckDNS answers for **every name under yours** (`www.`, `api.`, `shop.`) with the same number. That is how one server hosts three sites: the browser sends the name it wants, and Caddy picks the container for it.

!!! real "Real world — a free name is fine, a bought one is sturdier"
    `duckdns.org` is on the Public Suffix List, so browsers treat `dwarpal-age.duckdns.org` as a site of its own, exactly like a bought domain. But DuckDNS is run by volunteers. When real websites depend on Dwarpal, a bought domain (a few hundred rupees a year) is the safer home (§5.8.2 lists what moving involves).

## 6.8 Caddy and the padlock

**Caddy** is the only container the internet can reach. It does two jobs:

1. **The padlock.** The first time someone visited, Caddy proved to **Let's Encrypt** (a free, non-profit certificate authority) that it really controls `dwarpal-age.duckdns.org`. Let's Encrypt asks for a secret answer to be shown at that address, and only the real server can show it. Let's Encrypt then signed a **certificate** valid for 90 days (ours: until 8 February 2027). Caddy renews it by itself about a month before it ends. The certificate is what makes browsers show `https://` and the padlock, and it encrypts everything between visitors and the server (§0.9).
2. **The receptionist.** It looks at which name each visitor asked for and passes the request to the right container on the server's private network (`reverse_proxy`). It also tells browsers to use HTTPS only, for two years (HSTS).

## 6.9 What is running, and what opens where

### Type an address on any phone or computer, and you get:

| Address | What opens | Served by |
| :-- | :-- | :-- |
| `https://dwarpal-age.duckdns.org` | **Dwarpal's home page**: what it is, how it works, how it protects privacy | `web` |
| `https://dwarpal-age.duckdns.org/console` | **The console**, where website owners sign up, make projects and API keys, and see figures | `web` (pages) + `api` (data) |
| `https://dwarpal-age.duckdns.org/v/…` | **The verify page**, the camera check a visitor of a shop sees. Each check has its own link | `web` + `api` + `inference` |
| `https://www.dwarpal-age.duckdns.org` | Moves you to the address without `www.` | `caddy` |
| `https://api.dwarpal-age.duckdns.org` | **No page for people.** Programs talk to it in JSON (§0.11). `/readyz` answers `{"database":"ok","valkey":"ok"}` | `api` |
| `https://shop.dwarpal-age.duckdns.org` | **Amber Cellars**, the demo wine shop: "Verify my age to enter" | `shop` |

### Is Dwarpal a middleman that forwards visitors to the real site?

**No**, and this is worth getting exactly right. Dwarpal is **not** in front of other websites, and their visitors don't pass *through* it. It is a **service that websites call** when they need to know "is this person old enough?", the way a shop calls a bank to check a card. Here is one check on the demo shop, step by step:

1. A visitor opens **Amber Cellars** and clicks **Verify my age to enter**.
2. The **shop's server** calls Dwarpal's API with its secret **API key**: "please start an age check for me, and send the person back to me afterwards" (`POST /v1/verification-sessions`, which answered `201 Created` when tested that night).
3. Dwarpal answers with a one-time **verify link**. The shop opens it over its own page.
4. On Dwarpal's **verify page**, the visitor's camera takes a few frames. The AI checks they're a real, live person, not a photo or a screen, and estimates whether they're old enough. **The photos are checked once and never stored.**
5. Dwarpal sends the visitor back to the shop with a **signed answer** ("over 18: yes"), and nothing else: not the age, not the face, not a name.
6. The shop checks the signature and lets the visitor into the cellar.

!!! kid "Explain like I'm six"
    The wine shop is a cinema, and Dwarpal is the friendly lady at a booth next door who looks at your face and gives you a **stamped ticket** saying "old enough". She never writes down who you are. The cinema doesn't let you in through her booth; it just trusts her stamp.

### The twelve containers

| Container | Its job |
| :-- | :-- |
| `caddy` | The front door: HTTPS and passing requests on (§6.8) |
| `web` | The website's pages |
| `api` | The brain of the business: accounts, projects, keys, sessions, signed tokens |
| `inference` | The AI: faces, liveness, anti-spoofing, age estimate, ID-card reading |
| `postgres` | The database, where accounts, projects and check results are kept, **never photos** |
| `valkey` | Short-term memory: sign-in sessions, rate limits, check progress |
| `shop` | The demo shop |
| `webhooks` | Tells websites when a check finishes, if they asked to be told |
| `maintenance` | The cleaner: deletes old records when their retention time is up |
| `collector`, `prometheus`, `alertmanager` | The alarm system (§6.11) |

## 6.10 How everyone proves who they are

Tonight used **eight different ways of proving identity**. They are worth seeing side by side:

| Who proves | To whom | How |
| :-- | :-- | :-- |
| You | The server | **SSH key** `dwarpal`: a signature, the private key never leaves the laptop |
| GitHub's deploy robot | The server | **SSH key** `dwarpal_deploy`, kept as a GitHub secret |
| The server | You and GitHub | Its **host key**, remembered in `known_hosts` and `DEPLOY_KNOWN_HOSTS` |
| Caddy | Let's Encrypt | Showing a secret answer at the domain (the **ACME challenge**) |
| The server | Visitors' browsers | The **certificate** Let's Encrypt signed |
| A website owner | The console | **Email and password.** The password is stored only as an **Argon2id** hash: slow and memory-heavy on purpose, so a stolen database is useless for guessing (§5.4.5). Optional six-digit **authenticator codes** (TOTP), and **passkeys** that need no password at all (§5.9.2). After five wrong tries, that network address must wait, longer each time |
| A website (the shop) | The API | Its **API key**, `dk_test_…` for testing or `dk_live_…` for real checks. Dwarpal stores only a fingerprint of it, so it is shown just once, at creation |
| The server | Gmail, Oracle Object Storage | A Gmail **app password**, and an Oracle **customer secret key** (§6.11, §6.12) |

A visitor checking their age proves **nothing about who they are**: no account, no name. Dwarpal only learns "old enough or not".

**Moving the shop's key without showing it.** The console shows a new API key only once. You copied it, and instead of pasting it into the chat, a small command read it from the clipboard and sent it straight into the server's `.env` over SSH. It was never displayed. (The first try found something else on the clipboard; the second time it was the key.)

## 6.11 Alerts: a friend who phones you

Three containers watch the system from inside. The **collector** gathers the API's measurements, **Prometheus** stores them and checks the alert rules (§5.8.4), and **Alertmanager** sends an email when a rule fires: too many errors, slow face checks, or measurements that stopped arriving. A second email follows when the problem is over.

To send email it needs a mail account. You chose a separate Gmail account for this. Google doesn't allow programs to use your normal password, so it gives **app passwords**: 16 letters that work only for sending mail, and can be deleted any time without changing your real password. They need **2-Step Verification** to be on.

!!! warn "Careful — where you paste matters"
    The first time, the app password was pasted into PowerShell's prompt instead of the server's *password* prompt. PowerShell treated it as a command, showed it on screen and saved it in its history file. A password that has been displayed counts as leaked, so it was **deleted at Google and replaced** with a new one, and the history line removed. A prompt that hides what you type says so: *"(not shown)"*.

A test alert was sent through Alertmanager, and it arrived. The outside check (§5.8.5) is GitHub's *uptime* robot: every 15 minutes it asks the API and the home page whether they're alive, and GitHub emails the owner if they aren't. That covers the one case the inside alarms can't, the whole server being down.

## 6.12 Backups: a copy in another building

If the server's disk broke tomorrow, every account and project would be gone. So every night at **02:00 IST**, a **systemd timer** (Linux's built-in alarm clock) runs `backup.sh`:

1. PostgreSQL makes a **dump**, the whole database as one file.
2. **restic**, a backup program, **encrypts** it on the server with a long random password, and only then sends it to **Oracle Object Storage**, in the bucket `dwarpal-backups`. The `.env` secrets go the same way, because the master key in it is needed to read the database's signing keys.
3. Old backups are thinned out (7 daily, 4 weekly, 6 monthly) and the remaining ones are checked for damage.

The storage is reached through its **S3-compatible** interface, the way Amazon's storage works, which most backup programs understand. For that, Oracle gave a **customer secret key** in two parts: an *access key* (like a username, not secret on its own) and a *secret* (shown only once). The restic password was made on the server, and shown to you once in a terminal so you could keep a copy **offline**: without it, no backup can ever be read, by anyone, including you.

!!! real "Real world — three things that went wrong, and what they taught"
    1. **The clipboard held the wrong thing.** You copied the access key to send it, and it replaced the secret on the clipboard. The server received the access key twice. A check that compares the two (without printing either) found it, and the secret was copied again from Notepad.
    2. **A brand-new key works only some of the time.** For several minutes after it is made, some of Oracle's servers accept it and others don't: tests showed *ok, denied, denied, ok, denied, ok*. A small loop waited for eight successes in a row (17 tries) before backing up.
    3. **"Access Denied" was really "wrong region".** Oracle's storage accepts only requests *signed for its own region*, and restic didn't work out `ap-hyderabad-1` from the address by itself. A signed test request written by hand showed the key was fine; telling restic the region (`-o s3.region=…`) fixed it. `backup.sh` and `restore_drill.sh` now read the region from the storage's address (their walkthroughs explain the lines).

**The restore drill.** A backup nobody has restored is only a hope. `restore_drill.sh` downloaded the newest backup, decrypted it into a **throwaway** database, counted every table, and deleted the throwaway. It came back whole: migration `0013`, one user, one organisation, two projects, one API key, one signing key, the audit log. This was Phase 8's exit test, and it passed on the first try. The report is in `docs/reports/phase-8.md`.

## 6.13 The night in order

| # | Step | Who |
| :-- | :-- | :-- |
| 1 | Made two SSH key pairs on the laptop | You (`ssh-keygen`) |
| 2 | Made the network (VCN) with the wizard; checked ports 22/80/443 were open | You, in Oracle |
| 3 | Upgraded to Pay As You Go to get past "out of capacity"; set a ₹100 budget alert; asked Oracle Support to refund the verification amount | You |
| 4 | Created the instance: Ubuntu 24.04, A1.Flex 2 cores / 12 GB, public IP, your public key, no cloud-init | You |
| 5 | Logged in over SSH; firewall, updates, Docker, swap, key-only SSH | Assistant, over SSH |
| 6 | Copied deploy files and models; made the secrets on the server; added the deploy key | Assistant |
| 7 | Pointed `dwarpal-age.duckdns.org` at the server | You, on DuckDNS |
| 8 | Added the GitHub variables, the secret and the `production` gate | You, on GitHub |
| 9 | Ran the deploy workflow: four images built and published; checked they're public; approved the deploy | You; checks by the assistant |
| 10 | Checked: HTTPS certificate, `/readyz`, home page, console, anti-spoofing loaded | Assistant |
| 11 | Signed up on the console; made the *Demo shop* project and a test key; key moved into `.env`; shop started; a real check session created | You + assistant |
| 12 | Alert emails: Gmail app password, Alertmanager started, test alert received | You + assistant |
| 13 | Backups: bucket, secret key, `backup.env`, first backup, nightly timer, restore drill | You + assistant |

!!! honest "Honest limitation"
    - **One server, one region.** If Oracle's Hyderabad building has an outage, Dwarpal is down until it's back. The Helm chart (§5.8.3) is ready for a bigger setup when it's needed.
    - **2 cores is only partly measured.** The load test met its target on 4 cores (§5.7.4). On this server a first, short run on 11 Nov (§6.14) timed everything except the real age model, and was cut short by Dwarpal's own per-address limit.
    - **No age model is certified yet.** Live checks are decided by an ID document until one is (decision D24); the demo shop uses a **test** key. Since 12 November the trained model decides those test checks (§6.15).
    - **The free name** depends on DuckDNS's volunteers (§6.7).
    - **Oracle may stop an idle free server** (§5.8.1). Dwarpal with few visitors looks idle by Oracle's measures; whether the upgraded account is spared isn't confirmed.
    - **The refund** of Oracle's verification amount was still open when this was written.

## 6.14 The morning after: three things the first real use found

The morning after launch, the owner used Dwarpal as a visitor would — and that found what no automatic check had.

**1. The check passed, but the shop wouldn't let them in.** The camera check finished with "You're all set", then the shop showed "Something went wrong". The shop's log said why: *unexpected "aud" claim value*. When a check passes, Dwarpal gives the shop a signed **pass token**, like a stamped ticket. The ticket names who it's for — its **audience** (`aud`) — so a ticket made for one website can't be used at another. The shop compares that name with its own project ID, and refuses a ticket made for anyone else.

Both names were the same project, written two ways. A database stores the ID as a UUID (`01a1c66b-…`); everything outside it — the console, the tokens — shows the shorter, public form (`prj_01M736PB…`), the same number in a different alphabet. On launch night the assistant copied the UUID into the server's settings (`DWARPAL_SHOP_PROJECT_ID`). So every check passed and every visitor was then turned away. It was fixed in a minute — the right form in `.env`, the shop restarted — and the shop now refuses to **start** with an ID in the wrong form (`apps/demo-shop/lib/config.ts`, with a test), so this mistake would stop a deploy instead of every customer.

!walk apps/demo-shop/lib/config.test.ts

**2. A forgotten console password.** The console has no "forgot password" page yet. The password itself can't be looked up: only its **hash** is stored (Argon2id, §5.4.5) — a fingerprint that can check a password but never turn back into one. So the owner set a new one with a small script run on the server, typing it into their own terminal: the script hashed it and saved the hash, and the assistant never saw the password. The change is recorded in the audit log.

**3. The first load test on the real server.** The test (§5.7.4) plays 50 people taking checks, each every 15–25 seconds, from the assistant's laptop, with a separate test key, revoked afterwards. Two things got in its way, and both are Dwarpal working as designed:

- **The stand-in age model** on the server accepts only the ready-made policies, so the test's own policy was refused; the test can now use an existing one (`DWARPAL_LOAD_POLICY`).
- **A safety limit**: one network address may take only 120 challenges an hour, to stop someone retrying endlessly. All 50 simulated people shared one address, so after a minute every further challenge was refused (`429`). Lifting it for the test was left for another day.

What the minute did measure, on 2 cores: creating a session, starting it and getting a challenge each took under 0.15 s (95th percentile); a face attempt took about 1.2 s typically and 2.5 s at worst — without the real age model, which on the laptop added about 0.4 s. In that first minute all 50 people sent their first attempt within about 10 seconds; the inference service, with its 2 workers, turned away 70 of 120 as busy (always safely: "try again", never a pass) while its CPU sat near 180 % of 200 %.

!!! honest "Honest limitation"
    The capacity target (50 people in a check, p95 under 1.5 s) is still unproven on this server: the run was short, from one address, without the real age model, and started everyone at once. A fair run needs the per-address limit raised for its few minutes, or many addresses.

## 6.15 Two days later: the trained age model goes onto the server

On launch night the server ran a **stand-in** age model: a tiny piece of code that pretends to estimate an age, so everything around it could be tested. The real, trained model stayed on the laptop. On **12 November 2026** it was put on the server too. This section is the whole of that change, because it is a good small example of "changing a live server by hand, safely".

**What the model is.** `age-convnext-tiny-2026.10.17` is one file, `model.onnx`, of 112 MB. It takes face pictures of 224 × 224 pixels and answers with 101 numbers per face: the chance that the person is 0, 1, 2 … 100 years old. It learnt from the FairFace photos and its pass marks were set on the UTKFace photos. Beside it sits `manifest.json`, the model's **label**: its name, its fingerprint, what it learnt from, its pass marks for each age line, and what it is allowed to decide.

**Why it wasn't there already.** Git is told to ignore every `.onnx` file (`.gitignore`), because Git is made for text, not for 112 MB of numbers. So the model is not on GitHub, and the deploy robot can't deliver it. It has to be carried by hand, like the six small models on launch night (§6.5).

**The four steps, all over SSH from the laptop:**

| # | Step | The command, in words | Why |
| :-- | :-- | :-- | :-- |
| 1 | Carry the two files | `scp` copied `manifest.json` and `model.onnx` into `/opt/dwarpal/models/registry/age/age-convnext-tiny-2026.10.17/` | The containers read their models from `/opt/dwarpal/models` |
| 2 | Check nothing broke on the way | `sha256sum model.onnx` on the server gave `fd92579c…`, the same fingerprint the manifest names | A file damaged in the copy would give a different fingerprint (§0.9) |
| 3 | Tell the server to use it | A dated copy of `.env` was kept, then two lines were added to it: `DWARPAL_AGE_MANIFEST=registry/age/age-convnext-tiny-2026.10.17/manifest.json` and `DWARPAL_INFERENCE_AGE_BACKEND=onnx` | Containers read their settings from `.env` only when they start. The first line tells the API which label to follow; the second tells the AI service to load a real model instead of the stand-in |
| 4 | Restart what reads those settings | `docker compose up -d` recreated `inference`, `api`, `webhooks` and `maintenance`, and waited until each said *healthy* | The database, the website, the shop and Caddy were not touched, so the site stayed up |

**How we know it worked.** Three checks, from the outside in:

1. Anyone can open `https://api.dwarpal-age.duckdns.org/.well-known/dwarpal-configuration`. It now says `"age_model":"age-convnext-tiny-2026.10.17"`, `"age_model_calibrated":false` and `"live_checks":"document"`.
2. The AI service's own health answer says `"age_model":"age-convnext-tiny-2026.10.17","antispoof":"loaded","ocr":"ready"`.
3. Inside the AI container, the whole face pipeline was built and the model was run once: 3 faces took about 1.1 seconds on one processor thread.

!!! key "Key idea — the label decides what the model may do, not the person who installs it"
    The manifest says `"calibrated": false`: this model has not met the release standard of at most 2 % wrong passes for every age and group. The API reads that one word. While it is `false`, a **live** check (a `dk_live_…` key) still starts at the ID document (decision D24), and only **test** checks (a `dk_test_…` key, such as the demo shop's) are decided by the model from the camera. Nobody has to remember this rule; putting the file on the server can't switch it off.

!!! honest "Honest limitation"
    - **Non-commercial only.** The manifest says `"permitted_use": "non-commercial research only"`, because of the photos it was calibrated on and the starting weights it was trained from. A free demo for learning and interviews is inside that. Charging websites is not: that needs a model trained and calibrated on data that allows it.
    - **A rebuilt server needs this step again.** `infra/deploy/README.md` (step 4) now lists it, so a server restored from backups gets the trained model and not the stand-in.
    - **Not yet measured under load.** The 1.1 seconds is one quiet run. The load test of §6.14 has not been repeated with the real model.
    - **It broke the demo shop**, and nobody noticed for a day: the three checks above all passed, and none of them was *a visitor starting a check*. §6.19 tells that story; the model was taken off the server again on 13 November until the shop could name its own policy.

**To go back to the stand-in**, on the server: delete those two lines from `/opt/dwarpal/.env` and run `docker compose up -d api inference webhooks maintenance` in `/opt/dwarpal`.

!!! warn "Careful — every command belongs to one computer and one shell"
    That last command was first pasted into **Windows PowerShell on the laptop**, and failed with *"The token '&&' is not a valid statement separator"*. Two things were wrong, and both are worth knowing. First, the command was for the **server**: `/opt/dwarpal` and Docker Compose exist there, not on the laptop. To run it, you first log in with `ssh` (§6.3), and then you are typing in the server's shell. Second, `&&` ("do the next thing only if the first worked") is a word of **Bash**, the shell on Linux. Windows PowerShell 5.1 doesn't know it. Nothing was harmed: PowerShell refused the whole line before running any of it. Before pasting a command, ask: *which computer is this for, and which shell is in front of me?* The prompt tells you: `PS C:\Users\anubh>` is PowerShell on the laptop; `ubuntu@dwarpal:~$` is Bash on the server.

## 6.16 One visit, start to finish: how the services work together

DuckDNS, Oracle, GitHub and Let's Encrypt never talk to each other. Each does one small job, and they only meet in two stories: **a visit** and **a deploy**. Follow each once and the whole thing fits in your head.

### The story of a visit

Someone types `https://shop.dwarpal-age.duckdns.org` on a phone.

| # | What happens | Who does it |
| :-- | :-- | :-- |
| 1 | The phone asks "what number has this name?" The question travels to DuckDNS's name servers, which answer `140.245.234.110` — the number typed into DuckDNS's page on launch night | **DNS / DuckDNS**. Its job ends here: no page, no picture, no byte of the visit ever passes through DuckDNS |
| 2 | The phone opens a connection to that number, at door **443** | The internet. That number belongs to Oracle, who gave it to our instance |
| 3 | The connection passes two walls: Oracle's **security list** outside the computer, then `iptables` inside it. Both let 443 through | **Oracle's network**, then **Ubuntu** |
| 4 | Docker hands whatever arrives at doors 80 and 443 to the **Caddy** container, the only container with doors to the outside | **Docker** |
| 5 | Before any page is sent, the phone says which name it wants, and Caddy shows its **certificate** for that name. The phone checks that Let's Encrypt signed it and that the name matches. Then the two agree on a secret key for this visit, and everything after is encrypted | **TLS**, the "S" in HTTPS. Let's Encrypt isn't asked during a visit: its signature on the certificate is enough |
| 6 | Caddy reads the name: `shop.` goes to the `shop` container, `api.` to `api`, the bare name to `web`. It passes the request along the server's private network | **Caddy** as a *reverse proxy* |
| 7 | The container answers; if it needs to, it asks others (`api` asks `postgres`, `valkey` and `inference`). The answer returns the way it came | **The containers** |

So the name is only a **signpost** to the number. If the server ever got a new number, one field on DuckDNS's page would change and nothing else.

### The story of a deploy

| # | What happens | Who does it |
| :-- | :-- | :-- |
| 1 | You push code to GitHub, open *Actions → deploy* and press *Run workflow* | **You** |
| 2 | GitHub lends Arm computers that build the four images and put them on GHCR | **GitHub Actions** |
| 3 | The deploy step waits at the `production` gate until you approve | **GitHub**, then **you** |
| 4 | GitHub's robot logs in to the server over SSH: it finds the server by `DEPLOY_HOST` (the number, not the name), checks it is the real one with `DEPLOY_KNOWN_HOSTS`, and proves itself with `DEPLOY_SSH_KEY` | **GitHub Actions → the server** |
| 5 | On the server, `deploy.sh` downloads the new images from GHCR and restarts the containers, waiting for *healthy* | **The server ← GHCR** |

Notice the directions. GitHub **reaches in** to the server once, by SSH, to start the deploy. The server **reaches out** to GHCR to fetch images. Oracle only provides the computer both happen on. DuckDNS plays no part in a deploy at all.

### The four ways into the server, and who holds each key

| Way in | Door | Who can use it | What they can do |
| :-- | :-- | :-- | :-- |
| A browser | 443 (and 80, which only redirects to 443) | Everyone | See pages; call the API with a key |
| Your SSH key | 22 | Whoever holds `C:\Users\anubh\.ssh\dwarpal` | Everything on the server |
| The deploy SSH key | 22 | GitHub's deploy robot, after your approval | Everything the `ubuntu` user can, though it only runs `deploy.sh` |
| Oracle's website | — | Whoever can sign in to your Oracle account | Stop, restart or delete the whole computer |

That table is the whole **attack surface**: the complete list of what must be kept safe.

## 6.17 Where every key and secret lives

There is no single place called "the SSH key". There are several keys, each in exactly one or two places.

| Thing | Where it is | Secret? | If it's lost | If it's stolen |
| :-- | :-- | :-- | :-- | :-- |
| Your private SSH key | Laptop: `C:\Users\anubh\.ssh\dwarpal` | **Yes** | You can't log in. Oracle's console can still reach the instance, and a new public key can be added there | Remove its line from `authorized_keys` on the server, make a new pair |
| Your public SSH key | Laptop: `C:\Users\anubh\.ssh\dwarpal.pub`; server: a line in `/home/ubuntu/.ssh/authorized_keys` | No | Made again from the private key (`ssh-keygen -y`) | Nothing to fear |
| The deploy private key | Laptop: `C:\Users\anubh\.ssh\dwarpal_deploy`; GitHub: the secret `DEPLOY_SSH_KEY` | **Yes** | Deploys stop; make a new pair | Remove its line from `authorized_keys`; your own key still works |
| The deploy public key | Laptop: `dwarpal_deploy.pub`; server: a second line in `authorized_keys` | No | — | — |
| The server's host key | Server: `/etc/ssh/` (made by Ubuntu on first start); its public half on the laptop in `C:\Users\anubh\.ssh\known_hosts` and on GitHub in `DEPLOY_KNOWN_HOSTS` | Private half: yes | — | Someone could pretend to be the server |
| The app's secrets (database passwords, master key, shop key) | Server only: `/opt/dwarpal/.env`; an encrypted copy in each nightly backup | **Yes** | Restored from a backup | Change them all (the runbooks say how) |
| The token-signing keys (Ed25519) | In the database, locked with the master key from `.env`; their **public** halves at `/.well-known/jwks.json` for any website to check tokens with | Private halves: yes | New ones are made | Rotate them (the runbooks say how) |
| The backup password | Server: `/opt/dwarpal/backup.env`; your offline copy | **Yes** | **No backup can ever be read again** | Backups could be read by the thief |
| The HTTPS certificate and its key | Inside Caddy's storage on the server | Key: yes | Caddy asks Let's Encrypt for a new one by itself | Ask Let's Encrypt to revoke it |
| GitHub, Oracle, DuckDNS and Gmail sign-ins | In your head or password manager | **Yes** | Each site's "forgot password" | Change the password; turn on 2-step verification |

!!! key "Key idea — two unrelated things are both called Ed25519 here"
    **Ed25519** is a method for signing, and Dwarpal uses it in two places that have nothing to do with each other. Your **SSH keys** are Ed25519 keys: they prove *you* to the *server*. Dwarpal's **token-signing keys** are also Ed25519 keys: they prove to a *website* that an "old enough" answer really came from *Dwarpal*. Same maths, different keys, different jobs.

!!! try "Try it yourself"
    In PowerShell on the laptop: `Get-ChildItem $HOME\.ssh` lists the key files. `Get-Content $HOME\.ssh\dwarpal.pub` shows your public key: one line starting `ssh-ed25519`. It is safe to look at. **Don't** print the file without `.pub`. Then log in — `ssh -i $HOME\.ssh\dwarpal ubuntu@140.245.234.110` — and on the server run `cat ~/.ssh/authorized_keys`: two lines, and the first is the very line you just saw on the laptop. Type `exit` to come back.

## 6.18 If an interviewer asks

Short, true answers to the questions this deployment invites. Say them in your own words; the section in brackets is where the long answer is.

**"Walk me through your deployment."** One Arm virtual machine on Oracle Cloud's free tier, running Ubuntu. Twelve Docker containers started by Docker Compose. Caddy in front as the reverse proxy, ending HTTPS with a Let's Encrypt certificate. A free DuckDNS name points at the machine's public address. GitHub Actions builds the images, pushes them to GitHub's registry, and deploys over SSH behind a manual approval. Alerts by email, and encrypted backups every night to object storage, with a tested restore. (§6.1)

**"Why Oracle and not AWS?"** Its free tier gives an Arm machine with 12 GB of memory that never expires, enough to run the AI service. The free machines elsewhere are far smaller. (§6.2)

**"What is SSH, and how does key login work?"** An encrypted way to run commands on a remote computer. I hold a private key; the server holds the matching public key. The server sends a challenge, my computer signs it, the server checks the signature. The private key never leaves my laptop, and there is no password to guess. (§6.3)

**"Why two SSH keys?"** One for me, one for the deploy robot. If GitHub's secret ever leaked, I'd remove one line on the server and my own access would be untouched. That is *separation of duties*. (§6.3, §6.17)

**"What is `known_hosts` for?"** It stops a man in the middle. My laptop remembers the server's public host key from the first visit and refuses if it ever changes. (§6.3)

**"What is DNS? What does DuckDNS do?"** DNS turns names into addresses. DuckDNS is a free DNS provider: I own a name under `duckdns.org` and set which address it answers with. It only answers that one question; no traffic passes through it. (§6.7, §6.16)

**"How do three sites run on one machine with one address?"** Name-based routing. The browser sends the name it wants; Caddy reads it and forwards to the right container. DuckDNS answers every name under mine with the same address. (§6.8)

**"How does HTTPS get set up?"** Caddy asks Let's Encrypt for a certificate using the ACME protocol. Let's Encrypt checks that the server asking really controls the name, then signs a certificate for 90 days. Caddy renews it automatically. (§6.8)

**"What is a reverse proxy, and why have one?"** One front door for many services. It ends TLS in one place, routes by name, and keeps every other container off the internet. Only ports 22, 80 and 443 are open. (§6.4, §6.8)

**"Docker image against container?"** An image is the sealed, unchanging package of a program. A container is one running copy of it. I can throw a container away and start another from the same image and get the same program. (§0.14)

**"Why build the images on GitHub and not on your laptop?"** The server is Arm and my laptop isn't. GitHub has Arm build machines, so the image is built for the processor it will run on, the same way every time, from the exact commit. (§6.6)

**"How does a deploy fail safely?"** `deploy.sh` waits for every container's health check. If they aren't healthy in five minutes it goes back to the previous version. Database changes run as migrations before the new code starts. (§6.6)

**"Where are your secrets?"** Generated on the server, kept in one file readable by one user, never in Git. GitHub holds only the deploy key, as an encrypted secret. API keys are stored as fingerprints, passwords as Argon2id hashes. (§6.5, §6.10, §6.17)

**"How do you know when it breaks?"** From inside: Prometheus rules and Alertmanager emails. From outside: a scheduled GitHub workflow that checks the site every 15 minutes, which catches the whole server being down. (§6.11)

**"Have you ever restored a backup?"** Yes, as a drill, into a throwaway database, with every table counted. A backup that has never been restored is only a hope. (§6.12)

**"How did the AI model get to production?"** By hand, over `scp`, because model files are too big for Git. I checked its SHA-256 fingerprint against its manifest, switched two settings, and restarted only the containers that read them. (§6.15)

**"Is your model production-ready?"** No, and the system knows it. It is uncalibrated against the release standard and licensed for non-commercial research. The manifest says so, and the API reads the manifest: live checks fall back to an ID document, and only test checks use the model. (§6.15)

**"What would you change for real traffic?"** A bought domain. More than one machine, in more than one region — the Helm chart for Kubernetes is already checked in CI. A model trained on data licensed for commercial use, calibrated to the release standard. And a load test that passes on the real hardware. (§6.13)

**"What went wrong, and what did you learn?"** Pick one and tell it straight; interviewers remember these more than successes. The shop turned away every visitor who had passed, because a project ID was in the database's form and not the public form — fixed, and the shop now refuses to start that way (§6.14). An app password was pasted into the wrong prompt, so it was thrown away and replaced (§6.11). "Access Denied" from the backup storage was really a wrong region (§6.12).

**"Did you do all this yourself?"** The honest answer is the strong one: *"I built it with an AI coding assistant. I did every step in the cloud consoles myself, the assistant ran the server commands over SSH, and afterwards I made sure I understood each piece — I can explain any of it."* Then prove it with any answer above.

!!! try "Try it yourself"
    Cover the answers and say each one aloud. Then draw §6.1's picture from memory on paper. Where you get stuck is the section to read again.

## 6.19 The day the trained model broke the shop

On the night of 12–13 November the owner tried the demo, again and again, and got the same page every time: **"Something went wrong — we couldn't complete the age check on our side."** The model had been "working" on the server for a day (§6.15). This section is about how both of those were true at once.

**What the logs said.** The shop's log held the answer in one line, repeated for every try:

```text
DwarpalApiError: model age-convnext-tiny-2026.10.17 has no thresholds for age 18 at risk 0.02
  status: 422, code: 'policy_not_supported'
```

**What it means.** A website's **policy** says which age to check and how strict to be. The strictness is a **risk budget**: the largest share of under-age people that may wrongly pass. Every ready-made policy (`uk_osa_18` and the five others) asks for **2 %**. An age model's manifest lists **pass marks** (thresholds) for each pair of age and budget it has been calibrated for (§5.2). The stand-in model's manifest lists the presets' pairs. The trained model's lists what its calibration could honestly support:

| Age line | Risk budget the trained model has pass marks for |
| :-- | :-- |
| 13 and 16 | 15 % |
| 18 and 21 | 7.5 % |
| any, at the presets' 2 % | **none** |

So from the moment the trained model was switched on, the API refused **every preset policy** — correctly: it will not start a check it has no pass mark for. The shop's code named its policy as a fixed word, `uk_osa_18`. Every visitor was turned away before the camera opened.

!!! key "Key idea — "it's up" is not "it works""
    After the switch, three things were checked (§6.15): the public settings page named the new model, the AI service said it had loaded it, and the model ran on three faces. All three were about **parts**. Nobody did what a visitor does: press *Verify my age to enter*. A check of the parts is a **health check**; pressing the button is a **smoke test**. A change to a live system isn't done until the smoke test passes. The same lesson came the morning after launch (§6.14), in a different costume — which is the honest reason to write it down twice.

!!! honest "Honest limitation"
    This was known and forgotten. The load test's own file says, in a comment written weeks earlier, that the presets ask for a budget "this model can't yet promise, so the API would refuse them". The knowledge was in the repository; it was not in the checklist for switching models. It is now: the deploy guide's model step says to make a policy and test the shop.

**What was done, in order.**

1. **First, make it work again** (13 November, 00:40 IST). The two lines of §6.15 were commented out in `.env` — after a dated copy — and the four services restarted. The server was back on the stand-in model, and the shop's next request answered `201 Created`. Putting things back the way they last worked comes before understanding everything, and long before a better fix.
2. **Then, the real fix.** The shop's policy became a **setting**, `DWARPAL_POLICY` (in Compose: `DWARPAL_SHOP_POLICY` in `.env`), with the preset as its default. A name of the wrong shape stops the shop at start-up.
3. **To switch the trained model on again** (the deploy guide, step 4): deploy the new shop; switch the model on; in the console make a policy for the shop's project — `shop_18`, age 18, risk budget 7.5 % — which the API accepts only while the trained model is active; name it in `.env`; restart the shop; **and press the button**.

!!! real "Real world — what a 7.5 % budget feels like"
    With the trained model and that policy, the pass mark for "18 or over" is high: on the calibration photos, only about 13 % of real 18–20-year-olds and 30 % of 21–24-year-olds passed on the face alone; most were sent to the **document check** (§5.6). That is the design working — when the face can't settle it, a document does — and it is also the road to the Aadhaar demonstration of Part 7.
