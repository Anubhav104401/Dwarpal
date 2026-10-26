---
fingerprint: 1ca1a2c82662af30
---
The **organisation page** (`/console/org_…`). The part of the address in brackets, `[org]`, is a **dynamic segment**: Next.js passes whatever is there to the page as `params.org`.

@@ 1-2
The metadata type, and `notFound`, which shows the 404 page.

@@ 4
The page's contents.

@@ 6
The tab's title.

@@ 8
The shape of an organisation's public ID: `org_` and 26 characters.

@@ 10-11
Read the organisation from the address (Next.js 16 hands the parameters over as a promise).

@@ 12-14
An address that can't be an organisation's ID gets the 404 page at once, without asking the API.

@@ 15
Otherwise show the organisation.

@@ 16
End of the page.
