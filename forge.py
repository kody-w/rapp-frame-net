#!/usr/bin/env python3
"""
forge.py — the frame foundry (the global side of rapp-frame/1.0).

The Foundry, inverted: instead of manufacturing capability and pushing it fleet-wide,
this ingests each edge's append-only telemetry (GitHub Issues) and forges that edge's
next ECHO — its standing guidance until next contact — then commits it into the edge's
public-twin inbox and advances the swarm frame. Runs serverless as a GitHub Action, or
locally.

Echo forging is pluggable:
  - default: deterministic policy (acknowledges telemetry, sets a safe next aim) — no key.
  - FORGE_LLM=1 + a Copilot/GitHub token: a coordinating brainstem reasons about the
    telemetry to forge richer guidance (the production path).

Env: GITHUB_TOKEN (read issues + label), FRAME_NET (owner/repo). Commits via git.
"""
import hashlib
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

REPO = os.environ.get("FRAME_NET", "kody-w/rapp-frame-net")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = f"https://api.github.com/repos/{REPO}"
ROOT = os.path.dirname(os.path.abspath(__file__))


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _api(path, method="GET", data=None):
    req = urllib.request.Request(f"{API}{path}", method=method,
                                 data=(json.dumps(data).encode() if data else None),
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "Accept": "application/vnd.github+json",
                                          "User-Agent": "rapp-frame-forge"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _canon(d):
    return json.dumps({k: v for k, v in d.items() if k not in ("sig", "hash")}, sort_keys=True, separators=(",", ":"))


def _sha16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _telemetry_payload(issue):
    body = issue.get("body", "") or ""
    if "```json" in body:
        try:
            return json.loads(body.split("```json", 1)[1].split("```", 1)[0])
        except Exception:
            pass
    return {"raw": body[:500]}


def _forge_echo(node, telem, tick):
    """Forge the next echo for an edge from its latest telemetry."""
    obs = (telem.get("observations") or "")[:300]
    judged = (telem.get("judgment") or "")[:300]
    if os.environ.get("FORGE_LLM") == "1":
        try:
            return _forge_echo_llm(node, telem, tick)
        except Exception:
            pass
    guidance = (f"Acknowledged your tick-{telem.get('tick')} report. You observed: {obs or '(none)'}. "
                f"You judged: {judged or '(none)'}. Standing aim: continue what you judged sound, keep the node "
                f"healthy, and keep reporting. Escalate (observe-and-report, do not act) on anything irreversible "
                f"or anything that conflicts with these directives.")
    return {"spec": "rapp-frame-echo/1.0", "for": node, "tick": tick, "ack": f"telemetry@{telem.get('tick')}",
            "guidance": guidance, "constraints": ["prefer observe-and-report on irreversible actions"], "updated": _now()}


def _forge_echo_llm(node, telem, tick):
    raise NotImplementedError("wire a coordinating brainstem here (call_copilot over the telemetry)")


def _write(path, obj):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    json.dump(obj, open(full, "w"), indent=2)


def main():
    if not TOKEN:
        print("[forge] no GITHUB_TOKEN — nothing to ingest"); return
    issues = _api("/issues?state=open&labels=telemetry&per_page=100")
    by_node = {}
    for iss in issues:
        if "pull_request" in iss:
            continue
        t = _telemetry_payload(iss)
        node = t.get("node") or next((l["name"] for l in iss.get("labels", []) if l["name"].startswith("edge-")), None)
        if node:
            by_node.setdefault(node, []).append((iss["number"], t))
    # current tick
    latest = json.load(open(os.path.join(ROOT, "net/latest.json")))
    tick = latest.get("tick", 1)
    forged = 0
    for node, reports in by_node.items():
        num, telem = sorted(reports, key=lambda x: x[1].get("tick") or 0)[-1]
        echo = _forge_echo(node, telem, tick)
        _write(f"twins/{node}/inbox/latest.json", echo)
        _write(f"twins/{node}/state.json", {"node": node, "last_seen": _now(),
                                            "last_tick": telem.get("tick"), "status": "active"})
        for n, _ in reports:  # mark processed (auditable, append-only history preserved)
            try:
                _api(f"/issues/{n}", "PATCH", {"state": "closed", "labels": ["telemetry", "forged"]})
            except Exception:
                pass
        forged += 1
        print(f"[forge] forged echo for {node} (from telemetry #{num})")
    if forged:
        subprocess.run(["git", "-C", ROOT, "add", "-A"])
        subprocess.run(["git", "-C", ROOT, "-c", "user.name=frame-forge",
                        "-c", "user.email=forge@rapp-frame-net", "commit", "-m",
                        f"forge: {forged} echo(s) at tick {tick}"])
        subprocess.run(["git", "-C", ROOT, "push"])
    print(f"[forge] done — {forged} echo(s) forged")


if __name__ == "__main__":
    main()
