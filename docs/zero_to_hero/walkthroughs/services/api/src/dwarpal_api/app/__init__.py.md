---
fingerprint: 8e3d05310263c704
---
The marker file of the **use-case** layer (`app` is short for *application*).

@@ 1
The docstring: each step of a verification — create, start, challenge, attempt, finish — is written **once** here, as an ordinary function. The HTTP layer calls these functions. If one day the same steps had to be offered another way (a command-line tool, a message queue), the new front would call the very same functions, so the rules could never drift apart between the two.
