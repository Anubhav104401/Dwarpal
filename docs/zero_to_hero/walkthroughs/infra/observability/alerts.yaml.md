---
fingerprint: 3c1cc9e457641359
---
**The alert rules** (Phase 7, D11; design §11): Prometheus checks these every 15 seconds and marks an alert as *firing* when its condition holds. They watch the two promises the API makes: answer 99.9 % of requests without a server error, and keep a face attempt's 95th percentile within 1.5 seconds (NFR-05).

@@ 1-3
What this file is, and the two service levels it watches.

@@ 4-6
**Burn rates.** Allowing 0.1 % of requests to fail over a month gives an *error budget*. The burn rate is how fast it is being spent: at 1 it lasts exactly a month; at 14.4, 2 % of it goes in an hour. Each alert needs a long window and a short one to agree: the long one proves it isn't a blip, the short one that it is still happening (so the alert stops soon after the problem does). This is the approach of Google's *Site Reliability Workbook*.

@@ 7
Why `or vector(0)` appears below: while there has been no server error at all, the count of them doesn't exist, and dividing nothing by something gives nothing — an empty graph rather than 0.

@@ 8-10
One group of rules, named `dwarpal-slo` (SLO, *service level objective*: a promise expressed as a number).

@@ 11-14
A **recording rule**: Prometheus works out this expression on every check and stores the answer as a new series, `dwarpal:server_error_ratio:rate5m` (the colons are Prometheus's naming convention for such derived series). The expression: server errors per second (status codes matching `5..`, the 500s), or 0 if there are none, divided by all requests per second, both over the last 5 minutes. `>` lets the expression run over two lines.

@@ 15-26
The same share over 1 hour, 30 minutes and 6 hours — the four windows the two alerts need.

@@ 28-31
**`AvailabilityFastBurn`**: fires when the share over both the last hour and the last 5 minutes is above 14.4 times the allowance (14.4 × 0.001, so 1.44 %).

@@ 32-35
Its `severity` label is `page` — wake someone — and its summary says what is happening in words.

@@ 37-44
**`AvailabilitySlowBurn`**: 6 times the allowance over both 6 hours and 30 minutes — a slower leak that would still spend 5 % of the month's allowance in 6 hours. Its severity is `ticket`: deal with it in working hours.

@@ 46-50
**`FaceAttemptSlow`**: the 95th percentile of face attempts over 10 minutes, worked out from the duration histogram as on the dashboard, is above 1,500 ms.

@@ 51
`for: 10m` — and has stayed so on every check for 10 minutes, so a short spike doesn't fire it.

@@ 52-55
A ticket, with a summary that names the requirement it protects.

@@ 57-64
**`MetricsMissing`**: every other rule needs metrics to arrive. `up{job="dwarpal"}` is 0 when Prometheus couldn't collect from the collector; five minutes of that is an alert, marked `page` — without it, a broken pipe would look like a quiet, healthy service.
