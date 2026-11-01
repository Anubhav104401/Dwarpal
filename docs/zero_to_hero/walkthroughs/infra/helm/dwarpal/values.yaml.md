---
fingerprint: 1cdac7886460fec2
---
The **chart's settings** (§5.8.3), with the defaults. An install overrides what differs, such as `--set domain=example.org`.

@@ 1-4
What this file is — the chart's settings, each overridable at install time — and what the chart leaves out: PostgreSQL and Valkey, which a cluster normally gets as managed services.

@@ 6-7
The domain, from which every public address follows.

@@ 9-15
Where the images come from: GHCR, under the owner's account, with the tag (empty: the chart's version) and when to download them (only if missing).

@@ 17-19
The name of a **Secret** the cluster already holds — the `.env` values and the databases' addresses. Secrets are never written in a chart.

@@ 21-23
The models, from a read-only volume the cluster provides.

@@ 25-55
**The components**: for each, its image, the number of the unprivileged user its image runs as (Kubernetes checks it isn't root, and needs a number to do so), its port, the address that says it is healthy, how many copies to run, and its share of the computer — *requests* (what it is promised) and *limits* (the most memory it may use before it is stopped). The inference service gets a whole core and the most memory: it runs the neural networks.

@@ 57-60
**Autoscaling**: more copies of the API and the inference service when they are busy, between these numbers.

@@ 62-66
The cluster's **ingress controller** — its front door — and the Secret holding the HTTPS certificates.
