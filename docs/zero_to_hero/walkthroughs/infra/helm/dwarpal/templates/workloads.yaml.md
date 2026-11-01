---
fingerprint: a9ca21c4a33577ba
---
**The four services' workloads** (§5.8.3): a Deployment and a Service for each of the API, the inference service, the web app and the demo shop, from one template.

@@ 1-2
One template for all four services: `range` repeats everything until `end` for each component in `values.yaml`, with its name in `$name` and its settings in `$c`. Inside a `range`, `$` is the chart's top level.

@@ 3-5
`---` starts a new document; this one is a **Deployment** — "keep this many copies of this container running".

@@ 6-10
Its name (the release's name and the component's), and labels: the chart's shared ones (`_helpers.tpl`), and which component it is.

@@ 11-16
How many copies, and how the Deployment finds its own pods: by those two labels.

@@ 17-22
The **pod template** — what each copy looks like — labelled the same way.

@@ 23-27
The pod's security: never as root, as the image's own unprivileged user, with the kernel's default filter on system calls (`seccomp`).

@@ 28-33
The container: its name, its image (`dwarpal.image` builds `ghcr.io/<owner>/<image>:<tag>`), when to download it, and its port.

@@ 34-36
Every value of the Secret becomes an environment variable.

@@ 37-48
The settings that follow from the chart: production mode; the public addresses (for tokens, links and CORS); the private addresses of the inference service and the API, by their Service names; the demo shop's address; and where the models are. Each service reads the ones it knows and ignores the rest.

@@ 49-52
The container's own security: it can't gain privileges, can't change its own files, and has none of Linux's special powers.

@@ 53-60
**Probes**: the pod receives traffic only once its health address answers (*readiness*), and is restarted if it stops answering (*liveness*, after 30 seconds of grace).

@@ 61-62
Its share of the computer, copied from `values.yaml` (`toYaml` writes it out, `nindent` indents it).

@@ 63-67
What is mounted: the models, read-only; `/tmp`; and Next.js's cache folder, which the web apps write to while running.

@@ 68-75
The volumes behind them: the models' claim, read-only; and two small areas held **in memory** (`medium: Memory`), so nothing is ever written to disk.

@@ 76-89
A **Service** for the component: a stable private address (its name) and port, in front of whichever copies are running.

@@ 90
The end of the `range`.
