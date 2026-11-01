---
fingerprint: 201b77216564e6ab
---
The **server's first-boot setup** (Phase 8, §5.8.1), for Oracle Cloud's Always Free Ampere machine. Cloud servers read a file like this once, when they first start, through a program called **cloud-init**: so the server comes up already hardened and ready for Docker, with nothing typed by hand.

!!! key "Key idea — the server is described, not hand-made"
    Everything that makes the server safe is written here, reviewed like code, and applied the same way every time. If the server is ever lost, a new one made with this file is the same server.

@@ 1
`#cloud-config` — the first line **must** say this: it tells *cloud-init*, the program that prepares a new cloud server on its first boot, that the rest is its configuration (YAML).

@@ 2-5
What the file is for: Oracle's Always Free Ampere machine (decision O2b) running Ubuntu 24.04 for Arm processors; where to paste it when creating the server; and that the SSH key goes in the console's own box, which gives it to the default user `ubuntu`.

@@ 7-11
Refresh the list of packages and install every available update before anything else: a new server starts from an image that may be weeks old.

@@ 12-18
The packages, all from Ubuntu's own archive:
- `docker.io` and `docker-compose-v2` — Docker, which runs each service in its container, and Compose, which starts them together from one file (ADR-0015);
- `unattended-upgrades` — installs security updates by itself;
- `iptables-persistent` — saves the firewall's rules so they survive a restart;
- `ca-certificates` and `curl` — the trusted certificate authorities, and a tool to fetch web addresses (for health checks).

@@ 20-21
The server keeps time in UTC: logs and certificates then never depend on a time zone.

@@ 23-27
**`write_files`** — files cloud-init writes before running commands. First, an SSH setting file in the folder that SSH reads its extra settings from (`sshd_config.d`), readable by all, writable by root (`0644`).

@@ 28-32
**SSH: keys only.**
- no passwords and no keyboard-typed answers: a password can be guessed by the bots that try every server on the internet all day; a key can't;
- no logging in as `root`, the all-powerful user: you log in as `ubuntu` and ask for more with `sudo`;
- at most 3 tries per connection;
- no forwarding of graphical windows, which a server never needs.

@@ 34-38
**Automatic security updates**, in apt's settings folder.

@@ 39-43
Refresh the package list and install updates every day (`"1"`); if an update needs a restart, restart at 21:30 UTC — 03:00 in India, when fewest people are checking their age; and remove packages nothing needs any more.

@@ 45-48
**Docker's settings**: each container's log file is capped…

@@ 49-53
…at 10 MB, with 3 old files kept, so a chatty container can never fill the disk; and `live-restore` keeps containers running while Docker itself restarts (during its own updates).

@@ 55-58
**`runcmd`** — commands cloud-init runs once, as root, after writing the files. First the firewall: Oracle's Ubuntu images come with `iptables` rules that admit only SSH and reject everything else.

@@ 59-61
Insert three rules at position 5 — before the image's final "reject everything" rule: new connections to port 80 (plain HTTP, which Caddy only uses to send people on to HTTPS), to port 443 over TCP (HTTPS), and over UDP (HTTP/3, HTTPS's newest form). Everything else stays shut.

@@ 62
Save the rules, so they apply again after every restart.

@@ 63-68
**A 4 GB swap file** — disk space the system may use as overflow memory if the services briefly need more than the 12 GB they have: reserve it, make it readable by root only, format it as swap, switch it on, and list it in `/etc/fstab` so it is switched on at every start.

@@ 69-71
Start Docker now and at every boot, and let the `ubuntu` user run it without `sudo` (membership of the `docker` group).

@@ 72-73
**Where the deployment will live**: `/opt/dwarpal`, owned by `ubuntu`, and closed to every other user (`0750`): its secrets file will be there.

@@ 74-75
Restart SSH so the keys-only settings apply. (The key you added in the console still works: that is the point.)

@@ 76-77
Leave a marker file: if it exists, every step above ran. Checking for it is the first thing to do after logging in.

@@ 79-83
**Restart once at the end** (`power_state`), so that a kernel updated by the upgrade above is the one running, with the message shown in the server's log. `condition: true` means always.
