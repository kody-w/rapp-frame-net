"""Append-only event store for rapp-frame/1.0 — the rappterbook-v2-state pattern.

All swarm state is an append-only event log: events/frame-{N}.json (JSON arrays).
Views (net/latest.json, the frames, each twin's inbox echo + state) are DERIVED by
replaying events — never mutated directly. Read everything via raw.githubusercontent.com.

Stdlib only. Atomic writes (temp -> fsync -> rename). Concurrent-safe (fcntl.flock).
Adapted from kody-w/rappterbook-v2-state/scripts/event_store.py — same pattern.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_EVENT_TYPES: set[str] = {
    "edge.registered",      # an edge joins the net (publishes its twin)
    "telemetry.reported",   # an edge reports what it saw/judged/did (append-only)
    "echo.forged",          # the forge forges an edge's next echo from its telemetry
    "frame.started",        # a new swarm tick begins
    "frame.advanced",       # the swarm directive/world frame moves forward
    "system.snapshot",      # a full-state snapshot marker
}
REQUIRED_FIELDS = ["frame", "type", "data"]


def generate_event_id() -> str:
    return f"evt-{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _events_dir(state_dir: Path) -> Path:
    return Path(state_dir) / "events"


def _frame_path(state_dir: Path, frame: int) -> Path:
    return _events_dir(state_dir) / f"frame-{frame}.json"


def validate_event(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in event:
            errors.append(f"Missing required field: {field}")
    if "type" in event and event["type"] not in VALID_EVENT_TYPES:
        errors.append(f"Invalid event type: {event['type']}")
    if "frame" in event and not isinstance(event["frame"], int):
        errors.append("frame must be an int")
    if "data" in event and not isinstance(event["data"], dict):
        errors.append("data must be a dict")
    return errors


def _fill(event: dict[str, Any]) -> dict[str, Any]:
    e = dict(event)
    e.setdefault("id", generate_event_id())
    e.setdefault("timestamp", now_iso())
    e.setdefault("node_id", None)
    return e


def _read_locked(p: Path) -> list[dict[str, Any]]:
    if not p.exists():
        return []
    with open(p, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            c = f.read()
            return json.loads(c) if c.strip() else []
        except json.JSONDecodeError:
            return []
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _write_atomic(p: Path, events: list[dict[str, Any]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(events, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp, str(p))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_event(state_dir, event: dict[str, Any]) -> dict[str, Any]:
    """Validate, fill defaults, append to the frame's event file (locked + atomic)."""
    errs = validate_event(event)
    if errs:
        raise ValueError("invalid event: " + "; ".join(errs))
    e = _fill(event)
    p = _frame_path(Path(state_dir), e["frame"])
    p.parent.mkdir(parents=True, exist_ok=True)
    # exclusive lock across the read-modify-write
    with open(p, "a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            lock.seek(0)
            content = lock.read()  # read under the SAME held lock (no nested flock -> no deadlock)
            try:
                events = json.loads(content) if content.strip() else []
            except json.JSONDecodeError:
                events = []
            events.append(e)
            _write_atomic(p, events)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return e


def read_all_events(state_dir) -> list[dict[str, Any]]:
    """Replay: every event across every frame file, in (frame, timestamp) order."""
    d = _events_dir(Path(state_dir))
    if not d.exists():
        return []
    frames = sorted(int(f.stem.split("-")[1]) for f in d.glob("frame-*.json"))
    out: list[dict[str, Any]] = []
    for fr in frames:
        out.extend(_read_locked(_frame_path(Path(state_dir), fr)))
    out.sort(key=lambda e: (e.get("frame", 0), e.get("timestamp", "")))
    return out


def count_events(state_dir) -> int:
    return len(read_all_events(state_dir))
