#!/usr/bin/env python3
"""Fail-closed tombstone for the retired frame-net edge agent."""

from __future__ import annotations

import json
import sys
from typing import NoReturn

EXIT_RETIRED = 78
AUTHORITY_COMMIT = "6723c7add2aed36bb68992fc71a56b0a4bd5ad81"


class RetiredProtocolError(RuntimeError):
    """Raised whenever a caller attempts to use the retired edge path."""


def retired_status() -> dict[str, object]:
    return {
        "status": "retired",
        "active": False,
        "network": False,
        "authority_commit": AUTHORITY_COMMIT,
        "reason": (
            "The legacy frame-net cannot authenticate RAPP/1 swarm frames "
            "without the estate-owner registry and signing authority."
        ),
    }


class EdgeNodeAgent:
    """Compatibility name that refuses every former agent action."""

    name = "EdgeNode"
    metadata = {
        "name": name,
        "description": "Retired protocol path; no actions are available.",
        "parameters": {"type": "object", "properties": {}},
    }

    def perform(self, **_kwargs: object) -> NoReturn:
        raise RetiredProtocolError(retired_status()["reason"])


def main() -> int:
    print(json.dumps(retired_status(), sort_keys=True), file=sys.stderr)
    return EXIT_RETIRED


if __name__ == "__main__":
    raise SystemExit(main())
