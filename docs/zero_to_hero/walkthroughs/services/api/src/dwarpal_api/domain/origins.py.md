---
fingerprint: aac992fac4dab2ef
---
**Origins, written one way** (decision D29, 8 Nov 2026): the rules for a project's allowed origins, and for reading a return address's origin.

@@ 1-2
The module's docstring: web **origins** — `scheme://host[:port]` — written one way, so a project's allowed origins and a session's return address can be compared as plain text (decision D29). Pure rules, no input or output.

@@ 4
The project-wide type-hint setting.

@@ 6-8
Reading IP addresses, patterns, and cutting an address into its parts.

@@ 10-12
At most 10 origins a project; the names of this computer (`localhost`, in its three spellings); and the port each scheme uses when none is written.

@@ 13-14
**`HOST_NAME`** — a host name: labels of letters, digits and inner hyphens, 1 to 63 characters each, joined by dots. International names come in their `xn--` form, as browsers send them. No `*`: wildcards are refused.

@@ 17-18
**`InvalidOriginError`** — not an origin a project may allow; its message says what is wrong, in words a person can act on (the API shows it to them).

@@ 21-28
**`_host`** — a host checked and written the standard way: an IP address as Python writes it (an IPv6 one in brackets, as in addresses), otherwise a host name that fits `HOST_NAME` and the 253-character limit.

@@ 31-33
**`origin_of`** — an address's origin, written as browsers write it.

@@ 34-37
The address cut into parts; the scheme and host in lower case. Only `http` and `https`, with a host.

@@ 38-43
The port: Python refuses an impossible one with `ValueError`, and accepts `0`, which no website listens on — both are refused.

@@ 44-47
The host, and the port only if it isn't the scheme's usual one: `https://shop.example:443` and `https://shop.example` are the same origin, so both are written the second way.

@@ 50-52
**`allowed_origin`** — one origin a project may allow: only an origin, and `https`, except `http` for this computer while developing.

@@ 53-57
No user name or password, and nothing after the host and port (a lone `/` is forgiven).

@@ 58-61
The origin written the standard way; `http` refused in production, and anywhere but this computer.

@@ 62
The checked origin.

@@ 65-70
**`allowed_origins`** — a project's whole list: each checked, duplicates dropped (`dict.fromkeys` keeps the first of each, in order), and at most 10.
