---
fingerprint: 1acb78aa17a7a95d
---
The address `/console/org_…/prj_…` (Phase 5, §5.5.2): a project's own page. Like the organisation page, it runs on the server only to check the address's shape, then hands over to the part that runs in the browser.

@@ 1-2
Next.js's type for a page's title, and `notFound`, which shows the "not found" page.

@@ 4
The part of the page that runs in the browser.

@@ 6
The browser tab's title.

@@ 8-9
The shapes of an organisation's and a project's public ID: the prefix, then 26 letters and digits.

@@ 11
The page itself. Next.js passes the address's two changing parts — `[org]` and `[project]`, the folders' names — as `params`, which arrives later (a `Promise`), so the function is `async`.

@@ 12
Wait for them, and take both out.

@@ 13-15
If either isn't the right shape, show "not found" at once: no request is made with a made-up ID.

@@ 16
Otherwise, show the project.

@@ 17
End of the page.
