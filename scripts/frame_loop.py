#!/usr/bin/env python3
"""
frame_loop.py — the central frame loop (forge + materialize) for rapp-frame/1.0.

The rappterbook-v2-state pattern: replay the append-only event log, forge each edge's
next echo from its latest telemetry (the Foundry, inverted), then MATERIALIZE the views
edges read via raw — each twin's inbox echo + state, and views/events.json. Idempotent:
running it twice yields identical views. Views are never primary data; the log is.

Runs serverless as a GitHub Action, or locally:  python3 scripts/frame_loop.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from event_store import read_all_events, append_event, now_iso  # noqa: E402

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _write_atomic(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
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


def _forge_guidance(t):
    obs = (t.get("observations") or "")[:300]
    jud = (t.get("judgment") or "")[:420]
    return (f"Acknowledged your tick-{t.get('tick')} report. You observed: {obs or '(none)'}. "
            f"You judged: {jud or '(none)'}. Standing aim: continue what you judged sound, keep the node "
            f"healthy, keep reporting. On anything irreversible or anything that conflicts with the directives — "
            f"observe and report, do not act.")


def main():
    events = read_all_events(ROOT)
    latest_telem, echo_ack = {}, {}
    for e in events:
        if e["type"] == "telemetry.reported":
            n = e["data"].get("node")
            if n:
                latest_telem[n] = e
        elif e["type"] == "echo.forged":
            echo_ack[e["data"].get("for")] = e["data"].get("ack")

    # forge: any node whose latest telemetry isn't yet answered by an echo
    forged = 0
    for n, te in latest_telem.items():
        ack = f"telemetry@{te['data'].get('tick')}#{te['id']}"
        if echo_ack.get(n) != ack:
            echo = {"spec": "rapp-frame-echo/1.0", "for": n, "tick": te["data"].get("tick"), "ack": ack,
                    "guidance": _forge_guidance(te["data"]),
                    "constraints": ["prefer observe-and-report on irreversible actions"], "updated": now_iso()}
            append_event(ROOT, {"frame": te.get("frame", 1), "type": "echo.forged", "node_id": n, "data": echo})
            forged += 1

    # materialize views from the (now-updated) log
    events = read_all_events(ROOT)
    latest_echo, latest_telem = {}, {}
    for e in events:
        if e["type"] == "echo.forged":
            latest_echo[e["data"]["for"]] = e
        elif e["type"] == "telemetry.reported":
            n = e["data"].get("node")
            if n:
                latest_telem[n] = e
    for n, ee in latest_echo.items():
        _write_atomic(ROOT / "twins" / n / "inbox" / "latest.json", ee["data"])
    for n, te in latest_telem.items():
        _write_atomic(ROOT / "twins" / n / "state.json",
                      {"node": n, "last_seen": te["timestamp"], "last_tick": te["data"].get("tick"), "status": "active"})
    _write_atomic(ROOT / "views" / "events.json",
                  {"_meta": {"materialized_at": now_iso(), "event_count": len(events)}, "events": events[-100:]})
    print(f"[frame-loop] events={len(events)} forged={forged} nodes={sorted(latest_echo)}")


if __name__ == "__main__":
    main()
