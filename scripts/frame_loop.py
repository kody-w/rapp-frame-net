#!/usr/bin/env python3
"""Fail-closed tombstone for the retired frame forge/materializer."""

from __future__ import annotations

import json
import sys

EXIT_RETIRED = 78


def main() -> int:
    status = {
        "status": "retired",
        "active": False,
        "network": False,
        "writes": False,
        "reason": (
            "No forge can emit RAPP/1 swarm frames without an authenticated "
            "registry and estate-owner signing authority."
        ),
    }
    print(json.dumps(status, sort_keys=True), file=sys.stderr)
    return EXIT_RETIRED


if __name__ == "__main__":
    raise SystemExit(main())
