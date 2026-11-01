---
fingerprint: f4f64ea1c6e78bf1
---
**Scaling and network rules** (§5.8.3): more copies when busy, and the inference service — which sees faces — reachable only from the API.

@@ 1
What the file holds.

@@ 2-14
For each entry in `autoscaling`: a **HorizontalPodAutoscaler** for the Deployment of that name…

@@ 15-22
…keeping between the minimum and maximum copies, adding them when the average CPU use passes 70 %.

@@ 23-30
A **NetworkPolicy** for the inference service: by default anything in a cluster may talk to anything; this one says who may talk to it.

@@ 31-44
It applies to the inference service's pods, for traffic coming in: only from the API's pods, only on its port. The face frames reach it from nowhere else.
