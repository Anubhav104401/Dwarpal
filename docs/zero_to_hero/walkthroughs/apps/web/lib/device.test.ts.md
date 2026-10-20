---
fingerprint: 98c01d022e74b10b
---
Unit tests for the device ID (Vitest, §4.20), using a stand-in for the browser's storage.

@@ 1
Vitest's tools.

@@ 3
The function under test.

@@ 5-13
**`memory`** — a stand-in storage: a `Map` in memory, with the two methods `deviceId` uses. `?? null` returns `null` for a missing key, as real storage does.

@@ 15
A group of tests about the device ID.

@@ 16-21
**It is created once, then kept.** The first call makes a UUID (36 characters of hex digits and hyphens); the second call returns the same one.

@@ 23-26
**A malformed stored value is replaced** — here a scrap of HTML, which must never reach a request header — by a fresh UUID.

@@ 27
**With no storage**, there is no ID.

@@ 28-34
**With storage that refuses to store** (its `setItem` throws), there is no ID either — and no error escapes.

@@ 35-36
The end of the test and the group.
