---
fingerprint: 7d0d80a264a39f0f
---
**Roles** in the console (Phase 4, §5.4.5): who may do what in an organisation. The design's matrix (§3.7) is written here once, as data, and every console action asks it. The tests check every cell (`test_console_rules.py`).

| | owner | admin | developer | analyst |
| :-- | :-: | :-: | :-: | :-: |
| delete the organisation | ✅ | | | |
| manage members, read the audit log | ✅ | ✅ | | |
| manage keys, webhooks, policies | ✅ | ✅ | ✅ | |
| read sessions and analytics | ✅ | ✅ | ✅ | ✅ |

This is **role-based access control** (RBAC): permissions belong to roles, and people get roles, so nobody's rights have to be listed one by one.

@@ 1
The docstring: pure rules, with no database or network.

@@ 3
The project-wide type-hint setting.

@@ 5
`StrEnum` — a set of named values that are also ordinary text, so `Role.OWNER == "owner"`.

@@ 8-12
**`Role`** — the four roles.

@@ 15-23
**`Action`** — the eight kinds of thing a member might do.

@@ 26
`READ_ONLY` — what an analyst may do: look at sessions and analytics.

@@ 27
`BUILDING` — what a developer may do: everything read-only, plus manage keys, webhooks and policies. `|` joins two sets.

@@ 28-33
**`ALLOWED`** — the matrix. An owner may do every action (`frozenset(Action)` is the set of all of them); an admin every action but deleting the organisation (`-` removes from a set); a developer the building set; an analyst the read-only set.

@@ 36-37
**`can`** — may a member with this role do this action?

@@ 38-41
Look the role up and ask whether the action is in its set. A role that isn't one of the four (`Role(role)` raises `ValueError`) may do nothing: an unexpected value denies rather than allows — **failing closed**.
