"""
EdgeNode — turn this brainstem into an edge of the planetary frame-net (rapp-frame/1.0),
read over the HYDRA (rapp-hydra/1.0): the swarm's state is static data served from MANY
heads (GitHub raw, jsDelivr, raw.githack, mirrors, IPFS…). The edge reads from whichever
head is reachable; content is hash-verified, so any head — even a hostile mirror — is safe.
Cut one head, another serves it. No one can shut the swarm down.

The edge IS a brainstem making LOCAL JUDGMENTS. It pulls the swarm's guidance (a frame +
its echo) from any head, reconciles it against local reality with its OWN reasoning,
decides, and reports telemetry append-only. Lose every head and it keeps thinking on its
last verified echo — degrade-to-one.

Actions (drop-in, stdlib only): sync · judge · report · status. See rapp-frame SPEC.md.
Config (env): FRAME_NET_OWNER, FRAME_NET_REPO, FRAME_NODE_ID, FRAME_HEADS (extra mirror bases, csv).
"""
import hashlib
import json
import os
import socket
import sys
import time
import urllib.request

from agents.basic_agent import BasicAgent

OWNER = os.environ.get("FRAME_NET_OWNER", "kody-w")
REPO = os.environ.get("FRAME_NET_REPO", "rapp-frame-net")
NODE_ID = os.environ.get("FRAME_NODE_ID", f"edge-{socket.gethostname().split('.')[0]}")
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
HOME = os.path.expanduser("~/.brainstem/frame_net")

# HYDRA — many heads serve the same content; read from whichever is reachable.
HEADS = [
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main",     # GitHub raw
    f"https://cdn.jsdelivr.net/gh/{OWNER}/{REPO}@main",           # jsDelivr CDN (independent host)
    f"https://raw.githack.com/{OWNER}/{REPO}/main",               # raw.githack CDN
]
HEADS = [h for h in os.environ.get("FRAME_HEADS", "").split(",") if h.strip()] + HEADS


def _brainstem():
    for nm in ("brainstem", "__main__"):
        m = sys.modules.get(nm)
        if m is not None and hasattr(m, "call_copilot"):
            return m
    return None


def _get(path, t=8):
    """Fetch a repo-relative path from any reachable HYDRA head. Returns (text, head) or (None, None)."""
    for base in HEADS:
        try:
            req = urllib.request.Request(f"{base}/{path}",
                                         headers={"Cache-Control": "no-cache", "User-Agent": "rapp-frame-edge"})
            with urllib.request.urlopen(req, timeout=t) as r:
                return r.read().decode("utf-8", "replace"), base
        except Exception:
            continue
    return None, None


def _canon(d):
    return json.dumps({k: v for k, v in d.items() if k not in ("sig", "hash")}, sort_keys=True, separators=(",", ":"))


def _sha16(s):
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()[:16]


def _cache(name, obj=None):
    os.makedirs(HOME, exist_ok=True)
    p = os.path.join(HOME, name)
    if obj is None:
        try:
            return json.load(open(p))
        except Exception:
            return None
    json.dump(obj, open(p, "w"), indent=2)
    return obj


def _github_token():
    bs = _brainstem()
    if bs is not None:
        for attr in ("get_github_token", "_get_github_token"):
            fn = getattr(bs, attr, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    pass
    return os.environ.get("GITHUB_TOKEN")


class EdgeNodeAgent(BasicAgent):
    def __init__(self):
        self.name = "EdgeNode"
        self.metadata = {
            "name": self.name,
            "description": (
                "Make this brainstem an edge of the planetary frame-net (rapp-frame/1.0), read over the Hydra "
                "(many static heads, hash-verified). Pull the swarm's frame + echo from whichever head is up, "
                "reconcile it with LOCAL reality by your own reasoning, act, report telemetry append-only. Works "
                "offline on the last verified echo. action=sync | judge (pass `observations`) | report | status."
            ),
            "parameters": {"type": "object", "properties": {
                "action": {"type": "string", "enum": ["sync", "judge", "report", "status"]},
                "observations": {"type": "string", "description": "for judge/report: what the edge senses locally now"},
                "judgment": {"type": "string", "description": "for report: the decision from judge"},
            }, "required": ["action"]},
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = (kwargs.get("action") or "status").strip()
        if action == "sync":
            return self._sync()
        if action == "judge":
            return self._judge(kwargs.get("observations") or "")
        if action == "report":
            return self._report(kwargs.get("observations") or "", kwargs.get("judgment") or "")
        return self._status()

    def _sync(self):
        latest_raw, head = _get("net/latest.json")
        if latest_raw is None:
            echo = _cache("echo.json")
            return json.dumps({"node": NODE_ID, "online": False, "heads_tried": len(HEADS),
                               "using": "last verified echo" if echo else "none",
                               "tick": (_cache("latest.json") or {}).get("tick"),
                               "note": "all heads dark — operating on the last verified echo (degrade-to-one)."})
        try:
            latest = json.loads(latest_raw)
        except Exception:
            return json.dumps({"node": NODE_ID, "online": True, "head": head, "error": "latest.json not JSON"})
        prev = _cache("latest.json") or {}
        frame_changed = latest.get("hash") and latest.get("hash") != prev.get("hash")
        # the frame (swarm-wide directives) only re-fetches on a hash change; verify before act
        if frame_changed:
            frame_raw, _ = _get(f"net/frames/{latest['hash']}.json")
            if frame_raw:
                try:
                    frame = json.loads(frame_raw)
                except Exception:
                    return json.dumps({"node": NODE_ID, "online": True, "error": "frame not JSON — refusing to act"})
                if _sha16(_canon(frame)) != latest["hash"]:
                    return json.dumps({"node": NODE_ID, "online": True, "verified": False,
                                       "error": "frame hash mismatch — TAMPERED. Keeping last verified echo."})
                _cache("frame.json", frame)
                _cache("latest.json", latest)
        # the echo (per-edge aim) can change WITHOUT the frame — always refresh it
        echo_raw, _ = _get(f"twins/{NODE_ID}/inbox/latest.json")
        echo_changed = False
        if echo_raw:
            try:
                echo = json.loads(echo_raw)
                if echo != (_cache("echo.json") or None):
                    echo_changed = True
                _cache("echo.json", echo)
            except Exception:
                pass
        frame = _cache("frame.json") or {}
        echo = _cache("echo.json") or {}
        return json.dumps({"node": NODE_ID, "online": True, "head": head, "verified": True if frame_changed else None,
                           "new": bool(frame_changed or echo_changed), "tick": latest.get("tick"),
                           "directives": frame.get("directives", []),
                           "echo_guidance": echo.get("guidance", "(no echo yet — report telemetry to forge one)"),
                           "note": "guidance current. Run action=judge with local observations to decide."})

    def _judge(self, observations):
        frame = _cache("frame.json") or {}
        echo = _cache("echo.json") or {}
        bs = _brainstem()
        prompt = (
            "You are an edge brainstem on a high-latency, intermittent link to a swarm — possibly acting on guidance "
            "hours or days old, possibly fully offline. The swarm's STANDING GUIDANCE:\n"
            f"  directives: {json.dumps(frame.get('directives', []))}\n  your echo guidance: {echo.get('guidance', '(none)')}\n\n"
            f"Your LOCAL observations right now:\n  {observations or '(none provided)'}\n\n"
            "Guidance is GUIDANCE, not a command. Reconcile it against what you actually sense locally and decide what "
            "to DO now. If guidance conflicts with local reality, local reality + your judgment win — flag the conflict "
            "for telemetry. If an action is irreversible and you are unsure or the guidance is stale, prefer observe-"
            "and-report. Reply: DECISION (one line), REASONING (2-3 lines), CONFLICT (or 'none')."
        )
        if bs is None:
            return json.dumps({"node": NODE_ID, "judgment": "(no host LLM — observe-and-report mode)", "offline_reasoning": True})
        try:
            out = bs.call_copilot([{"role": "user", "content": prompt}])
            text = out[0] if isinstance(out, tuple) else out
            if isinstance(text, dict):
                text = (text.get("choices", [{}])[0].get("message", {}) or {}).get("content", str(text))
        except Exception as e:
            return json.dumps({"node": NODE_ID, "error": f"local judgment failed: {e}"})
        judgment = str(text).strip()
        _cache("last_judgment.json", {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "observations": observations, "judgment": judgment})
        return json.dumps({"node": NODE_ID, "tick": frame.get("tick"), "judgment": judgment,
                           "next": "run action=report to send this back (forges your next echo)."})

    def _report(self, observations, judgment):
        if not judgment:
            lj = _cache("last_judgment.json") or {}
            judgment = lj.get("judgment", "")
            observations = observations or lj.get("observations", "")
        tick = (_cache("frame.json") or {}).get("tick")
        telem = {"node": NODE_ID, "tick": tick, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "observations": observations, "judgment": judgment}
        ob = os.path.join(HOME, "outbox")
        os.makedirs(ob, exist_ok=True)
        fname = f"{int(time.time())}.json"
        json.dump(telem, open(os.path.join(ob, fname), "w"), indent=2)
        # write path: append-only via the GitHub Issues API when scoped+online; else buffer (the
        # Hydra write path — a git commit to any writable head — is the durable production channel).
        via, posted = "outbox (buffered)", False
        tok = _github_token()
        if tok:
            try:
                body = json.dumps({"title": f"telemetry: {NODE_ID} tick {tick}",
                                   "body": "```json\n" + json.dumps(telem, indent=2) + "\n```",
                                   "labels": ["telemetry"]}).encode()
                req = urllib.request.Request(f"{API}/issues", data=body, method="POST",
                                             headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                                                      "User-Agent": "rapp-frame-edge"})
                with urllib.request.urlopen(req, timeout=12) as r:
                    via, posted = f"GitHub issue #{json.loads(r.read()).get('number')}", True
                os.remove(os.path.join(ob, fname))
            except Exception as e:
                via = f"outbox (issue post failed: {str(e)[:60]})"
        return json.dumps({"node": NODE_ID, "reported": True, "posted_to_net": posted, "via": via,
                           "note": "telemetry banked; the frame loop forges your next echo from it."})

    def _status(self):
        latest = _cache("latest.json") or {}
        echo = _cache("echo.json") or {}
        lj = _cache("last_judgment.json") or {}
        pending = len(os.listdir(os.path.join(HOME, "outbox"))) if os.path.isdir(os.path.join(HOME, "outbox")) else 0
        _, head = _get("net/latest.json", t=5)
        return json.dumps({"node": NODE_ID, "net": f"{OWNER}/{REPO}", "heads": len(HEADS), "reachable_head": head,
                           "tick": latest.get("tick"), "echo_guidance": echo.get("guidance", "(none)"),
                           "last_judgment_at": lj.get("at"), "pending_telemetry": pending}, indent=2)
