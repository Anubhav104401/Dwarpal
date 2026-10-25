---
fingerprint: f830d06e7291d38f
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

@@ 5-8
`re` (to check names), `uuid`, `datetime`, `Any`.

@@ 10-12
From SQLAlchemy: `select` and `func` (for `max`), `IntegrityError` (the database refused a row, here for breaking a unique constraint), and the session types.

@@ 14-18
The tenant helper, the audit log (Phase 4, step 5), the two tables involved, the policy domain (the presets, the manifest, the `Policy` type, the uncalibrated error, `get_policy`) and our error class.

@@ 20
`NAME` — an acceptable name for a project's own policy: a lower-case letter, then 2 to 39 more lower-case letters, digits or `_`.

@@ 23-24
**`from_row`** — turn a table row into the `Policy` the decision engine already understands, with its version.

@@ 27-28
**`latest`** — which policy a **new** session gets for a name: the preset, or the project's newest version.

@@ 29-30
A preset's name always means the preset.

@@ 31-36
Otherwise, the project's versions of that name, newest first (`version.desc()`), and only the first (`limit(1)`).

@@ 37-39
None at all: refuse with `422 unknown_policy`.

@@ 40
Return it as a `Policy`.

@@ 43-44
**`pinned`** — the exact version a session was created with.

@@ 45-46
Version 0 means a preset.

@@ 47-53
Otherwise find the one row with the session's project, policy name and version number.

@@ 54-55
It must exist: versions can't be deleted (the database refuses), and a project's policies go only when the project itself does, taking its sessions with it. If it is missing anyway, refuse with `409` rather than guess at different rules.

@@ 56
Return it.

@@ 59-70
**`view`** — how a policy appears in the API: its `id` (the label, `shop_18@2` or `uk_osa_18`), its name and version, whether it is a preset, and its four rules.

@@ 73-82
**`add_version`** — add the next version of a project's policy. It takes the session factory, the model manifest, the project, the **draft** (the requested rules, as a `Policy` whose version is still 0), the time, a new ID, and — for the audit log — the project's organisation and who is acting.

@@ 83
Its docstring.

@@ 84-85
Refuse a badly shaped name, and a preset's name: `uk_osa_18` must always mean the preset.

@@ 86-89
The age model must have thresholds for this age and risk budget (§2.14), or no session could ever use the policy: refuse with `422 policy_not_supported`. Today's model is calibrated for 13, 16, 18 and 21 at 2 %.

@@ 90-97
Inside the project's tenant, find the newest version number of this name (`func.max`; `None` if there is none yet), and add one.

@@ 98-110
Add the new row: its ID, project, name, version number, the four rules, and the time.

@@ 111-112
Record it in the organisation's audit log, in the same transaction: the version's label as the target, and its rules as the facts.

@@ 113
Commit.

@@ 114-117
Two requests adding a version at the same moment could both compute "version 3". The unique constraint on project, name and version lets only one of them in; the other gets `IntegrityError`, answered as `409 policy_version_conflict`, try again.

@@ 118
Answer with the new version's view.

@@ 121-122
**`list_all`** — every policy the project can use: the presets, then each of its own policies' versions.

@@ 123-130
Read the project's versions, by name and then oldest version first.

@@ 131-132
The presets in alphabetical order, then the project's own, as one list.
