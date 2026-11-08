---
fingerprint: f9247dafbb7a5fe3
---
**Allowed origins, as typed** (8 Nov 2026): one helper shared by the organisation's and the project's pages.

@@ 1-2
**`originLines`** — a project's allowed origins as a person types them, one per line, in the list the API takes; the API checks each one (decision D29).

@@ 3-8
Split on line ends (`\r?\n`: Windows' or the others'), trim each line, and drop the empty ones.
