"""Who may do what in an organisation's console: four roles, and the actions each allows. Pure rules, no I/O."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"


class Action(StrEnum):
    DELETE_ORGANISATION = "organisation.delete"
    MANAGE_MEMBERS = "members.manage"
    MANAGE_PROJECTS = "projects.manage"
    READ_AUDIT = "audit.read"
    MANAGE_KEYS = "keys.manage"
    MANAGE_WEBHOOKS = "webhooks.manage"
    MANAGE_POLICIES = "policies.manage"
    READ_SESSIONS = "sessions.read"
    READ_ANALYTICS = "analytics.read"


READ_ONLY = frozenset({Action.READ_SESSIONS, Action.READ_ANALYTICS})
BUILDING = READ_ONLY | {Action.MANAGE_KEYS, Action.MANAGE_WEBHOOKS, Action.MANAGE_POLICIES}
ALLOWED: dict[Role, frozenset[Action]] = {
    Role.OWNER: frozenset(Action),
    Role.ADMIN: frozenset(Action) - {Action.DELETE_ORGANISATION},
    Role.DEVELOPER: BUILDING,
    Role.ANALYST: READ_ONLY,
}


def can(role: str, action: Action) -> bool:
    """Whether a member with `role` may perform `action`. An unknown role may do nothing."""
    try:
        return action in ALLOWED[Role(role)]
    except ValueError:
        return False
