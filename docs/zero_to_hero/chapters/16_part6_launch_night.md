# Part 6 — Launch night: putting Dwarpal on the internet

On the evening of **10 November 2026**, Dwarpal left the laptop and went live at **`https://dwarpal-age.duckdns.org`**. The owner had never used a cloud service or a server before. They clicked through Oracle's console, GitHub's settings, DuckDNS and Google's account pages, one instruction at a time, without knowing what most of the screens were for. This part explains **everything that happened that night, from zero**: every service, every key, every click, and how all of it fits together into one working website.

If you read only one part of this book to understand "how a website gets onto the internet", read this one.

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
3. **The AI models** (six files, about 25 MB): face finding, face landmarks, hand landmarks, face recognition, and the two **anti-spoofing** networks that spot a photo or a screen held up to the camera. They were copied from the laptop with `scp`. Without the anti-spoofing pair, every live check would be refused, so the first thing checked after the deploy was `"antispoof":"loaded"`.

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
    - **2 cores is unmeasured.** The load test met its target on 4 cores (§5.7.4); on this server it still needs measuring.
    - **No age model is certified yet.** Live checks are decided by an ID document until one is (decision D24); the demo shop uses a **test** key.
    - **The free name** depends on DuckDNS's volunteers (§6.7).
    - **The refund** of Oracle's verification amount was still open when this was written.
