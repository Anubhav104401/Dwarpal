---
fingerprint: bd890cb8407f4639
---
**Tests for origins** (decision D29).

@@ 1
What this file tests: origins written one way, what a project may allow, and how a return address's origin is read.

@@ 3
The project-wide type-hint setting.

@@ 5-7
pytest, and the rules under test.

@@ 10-22
Eight ways of writing an origin and what each becomes: capitals and a trailing `/` go, the usual port goes but another stays, an international name in its `xn--` form, IPv4 and IPv6 addresses (in brackets, in lower case), and spaces around.

@@ 23-24
Each is allowed, written as shown.

@@ 27-43
Twelve things that aren't origins a project may allow: a path, a query, a fragment, a user name, a wildcard, an underscore, ports 0 and 99999, another scheme, no scheme, `http` for another computer, nothing.

@@ 44-46
Each is refused — even while developing.

@@ 49-53
`http` for this computer is allowed while developing, and refused in production with a message about `https`.

@@ 56-63
A list keeps its order and drops a duplicate written another way; eleven origins are refused.

@@ 66-70
A return address is reduced to its origin, written the standard way; a `javascript:` address has no origin at all.
