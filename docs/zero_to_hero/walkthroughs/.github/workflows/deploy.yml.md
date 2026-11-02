---
fingerprint: 4635c79422b1350f
---
**Building and deploying** (Phase 8, §5.8.2), on GitHub: the four images built on Arm machines, published to GitHub's container registry (GHCR), and deployed to the server over SSH. Started by hand only.

@@ 1
The workflow's name, as GitHub's *Actions* tab shows it.

@@ 3-11
What it does, and **when**: only when started by hand (`workflow_dispatch`, the "Run workflow" button), never by itself — with one choice offered: deploy after building, or only build.

@@ 13-15
What this workflow may do with GitHub: read the code, and write **packages** — publish images to GHCR. Nothing else.

@@ 17-19
One deploy at a time: a second waits for the first rather than cancelling it halfway.

@@ 21-26
**The `images` job**, run on GitHub's own **Arm** machines (`ubuntu-24.04-arm`), so the server's Arm images are built natively — no slow emulation. 45 minutes at most.

@@ 27-33
A **matrix**: the job runs four times side by side, once per image — the API, the inference service, the web app and the demo shop — each with its Dockerfile and build argument.

@@ 34-38
Fetch the code, and set up uv at the project's version.

@@ 39-41
For the web app only, fetch the third-party models: its build copies the face landmarker for browsers.

@@ 42-45
Log in to GHCR with the token GitHub makes for this run alone, which expires when it ends. It is passed through an environment variable (never written into the command itself) and into `docker login` through its standard input, so it never appears in a command line or a log.

@@ 46-51
**Build and push.** The image's name, `ghcr.io/<owner>/dwarpal-<name>` (`${OWNER,,}` writes the owner in lower case, as GHCR requires), and its tag: the commit's first 12 characters.

@@ 52-55
The build arguments — the app to build, if any, and the API's public address (a repository *variable*, `DWARPAL_PUBLIC_API_URL`) — then the build, tagged both with the commit and `latest`.

@@ 58-60
Publish both tags.

@@ 62-68
**The `deploy` job** — only after the images are built, only if deploying was chosen, on an ordinary machine, in the `production` *environment*: GitHub can be set to wait for the owner's approval before any job that uses it.

@@ 69-70
Fetch the code again: the deploy files are copied from it.

@@ 71-75
The SSH key made only for deploys (a repository *secret*), the server's address, and its *host key* — what the server proves itself with, so the deploy can't be tricked into talking to another machine.

@@ 76-79
Write them where SSH looks, readable only by this job's user.

@@ 56-57
A **label** inside each image naming the repository it was built from (`org.opencontainers.image.source`, a standard label). GitHub's registry reads it and links the package to this repository, so the packages appear on the repository's page.

@@ 80-85
Copy this commit's Compose file, Caddy settings, the alerts' settings and rules (§5.8.4) and scripts to the server (`.env`, and the mail settings `alert_email.py` wrote, stay as they are), then run `deploy.sh` there with this commit's tag. If the new version isn't healthy, it rolls back and fails, and so does this job.
