---
fingerprint: ad0d3fd864846af0
---
**The API's dashboard** (Phase 7, D11, §5.7.7): four graphs of the metrics, loaded into Grafana from this file. JSON allows no comments, so everything is explained here. Each graph's *query* is written in **PromQL**, Prometheus's query language.

@@ 1
The start of the dashboard, a JSON object.

@@ 2-3
`uid` — a fixed identifier, so its address stays `/d/dwarpal-api` — and the title shown in Grafana.

@@ 4-6
By default, show the last hour; redraw every 30 seconds; and the version of Grafana's dashboard format this file is written in.

@@ 7
`panels` — the list of graphs.

@@ 8-11
The first: a time-series graph titled "Requests per second, by route". `gridPos` places it on Grafana's grid, which is 24 columns wide: from the left (`x: 0`) at the top (`y: 0`), half the width (`w: 12`) and 8 rows high.

@@ 12
Its data come from the Prometheus data source, found by the `uid` that `grafana-datasources.yaml` gave it.

@@ 13-18
Its query. `http_server_duration_milliseconds_count` is the running count of requests answered; `rate(…[5m])` turns it into requests per second, averaged over the last 5 minutes; `sum by (http_target)` adds those up per route, merging status codes. `legendFormat` names each line after its route.

@@ 19
The end of the first graph.

@@ 20-25
The second, at the top right (`x: 12`): the share of answers that were server errors. Its unit, `percentunit`, shows 0.001 as "0.1 %".

@@ 26
Its query is simply the recording rule from `alerts.yaml`, the share over 5 minutes — so the graph and the alerts can never disagree about the arithmetic.

@@ 27
The end of the second graph.

@@ 28-33
The third, bottom left (`y: 8`): the 95th percentile of response time per route, in milliseconds.

@@ 34-39
Its query. Durations are kept as a *histogram*: counts of requests that took up to 5 ms, up to 10 ms, and so on, each bucket labelled `le` ("less than or equal"). `histogram_quantile(0.95, …)` estimates from those counts the time that 95 % of requests beat, per route.

@@ 40
The end of the third graph.

@@ 41-45
The fourth, bottom right: the face attempts' 95th percentile, against the 1.5-second target of NFR-05.

@@ 46-58
Shown in milliseconds, with *thresholds*: green below 1,500, red from 1,500 (`null` means "from the very bottom"), drawn as a line across the graph (`thresholdsStyle`), so a glance shows whether the target is being met.

@@ 59-64
Its query: the same percentile as the third graph, but only for the face-attempt route and merged into a single line.

@@ 65-67
The end of the fourth graph, the list and the dashboard.
