---
fingerprint: dfee4794c3ec2a18
---
**Policies a website can choose** (Phase 4, §5.4.2). A policy is the set of rules for one kind of check: the age, the risk budget (how often a minor may wrongly pass, §2.14), how many face attempts a person gets, and how long the token lasts. Until now there were only the **presets**, built into the code (`domain/policy.py`). Now a project can also make its **own** policy — say `shop_18`, with one attempt instead of three.

The rule that shapes this file: **a policy version never changes.** Editing `shop_18` adds `shop_18@2`; version 1 stays exactly as it was. A session **pins** the version it was created with, so:

- a check already under way keeps the rules it started with, even if the website edits its policy halfway through;
- every result and token says exactly which rules it followed (`shop_18@1`), and those rules can still be looked up later, word for word.

The database enforces the rule too: the API's role may read and add versions, but not change or delete them (migration `0004`).

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-9
`re` (to check names), `uuid`, `replace` (a copy of a dataclass with one field changed), `datetime`, `Any`.

@@ 11-13
From SQLAlchemy: `select` and `func` (for `max`), `IntegrityError` (the database refused a row, here for breaking a unique constraint), and the session types.

@@ 15-19
The tenant helper, the audit log (Phase 4, step 5), the two tables involved, the policy domain (the presets, the manifest, the `Policy` type, the uncalibrated error, `get_policy`) and our error class.

@@ 21
`NAME` — an acceptable name for a project's own policy: a lower-case letter, then 2 to 39 more lower-case letters, digits or `_`.

@@ 24-33
**`from_row`** — turn a table row into the `Policy` the decision engine already understands, with its version and, since Phase 9, whether it accepts Age Passes.

@@ 36-37
**`latest`** — which policy a **new** session gets for a name: the preset, or the project's newest version.

@@ 38-39
A preset's name always means the preset.

@@ 40-45
Otherwise, the project's versions of that name, newest first (`version.desc()`), and only the first (`limit(1)`).

@@ 46-48
None at all: refuse with `422 unknown_policy`.

@@ 49
Return it as a `Policy`.

@@ 52-53
**`pinned`** — the exact version a session was created with.

@@ 54-55
Version 0 means a preset.

@@ 56-62
Otherwise find the one row with the session's project, policy name and version number.

@@ 63-64
It must exist: versions can't be deleted (the database refuses), and a project's policies go only when the project itself does, taking its sessions with it. If it is missing anyway, refuse with `409` rather than guess at different rules.

@@ 65
Return it.

@@ 68-80
**`view`** — how a policy appears in the API: its `id` (the label, `shop_18@2` or `uk_osa_18`), its name and version, whether it is a preset, its four rules, and (Phase 9) whether it accepts Age Passes.

@@ 83-92
**`add_version`** — add the next version of a project's policy. It takes the session factory, the model manifest, the project, the **draft** (the requested rules, as a `Policy` whose version is still 0), the time, a new ID, and — for the audit log — the project's organisation and who is acting.

@@ 93
Its docstring.

@@ 94-95
Refuse a badly shaped name, and a preset's name: `uk_osa_18` must always mean the preset.

@@ 96-99
The age model must have thresholds for this age and risk budget (§2.14), or no session could ever use the policy: refuse with `422 policy_not_supported`. Today's model is calibrated for 13, 16, 18 and 21 at 2 %.

@@ 100-107
Inside the project's tenant, find the newest version number of this name (`func.max`; `None` if there is none yet), and add one.

@@ 108-121
Add the new row: its ID, project, name, version number, the four rules, the time, and the Age Pass switch.

@@ 122-128
Record it in the organisation's audit log, in the same transaction: the version's label as the target, and its rules — the switch included — as the facts.

@@ 129
Commit.

@@ 130-133
Two requests adding a version at the same moment could both compute "version 3". The unique constraint on project, name and version lets only one of them in; the other gets `IntegrityError`, answered as `409 policy_version_conflict`, try again.

@@ 134
Answer with the new version's view: the draft, with its version number filled in (`replace` makes that copy).

@@ 137-138
**`list_all`** — every policy the project can use: the presets, then each of its own policies' versions.

@@ 139-146
Read the project's versions, by name and then oldest version first.

@@ 147-148
The presets in alphabetical order, then the project's own, as one list.
