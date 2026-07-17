#!/usr/bin/env python3
"""Fail-closed tombstone for the retired legacy event store."""

from __future__ import annotations

import json
import sys
from typing import NoReturn

EXIT_RETIRED = 78
VALID_EVENT_TYPES: frozenset[str] = frozenset()
REQUIRED_FIELDS: tuple[str, ...] = ()


class RetiredEventStoreError(RuntimeError):
    """Raised instead of reading or mutating historical state."""


def _retired() -> NoReturn:
    raise RetiredEventStoreError(
        "event_store is retired; committed event/state files are immutable evidence"
    )


def generate_event_id() -> NoReturn:
    _retired()


def now_iso() -> NoReturn:
    _retired()


def validate_event(_event: object) -> NoReturn:
    _retired()


def append_event(_state_dir: object, _event: object) -> NoReturn:
    _retired()


def read_all_events(_state_dir: object) -> NoReturn:
    _retired()


def count_events(_state_dir: object) -> NoReturn:
    _retired()


def main() -> int:
    status = {
        "status": "retired",
        "active": False,
        "mutation": False,
        "reason": "historical event/state artifacts are immutable evidence",
    }
    print(json.dumps(status, sort_keys=True), file=sys.stderr)
    return EXIT_RETIRED


if __name__ == "__main__":
    raise SystemExit(main())
