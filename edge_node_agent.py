"""
EdgeNode — turn this brainstem into an edge of the planetary frame-net (rapp-frame/1.0).

The edge IS a brainstem making LOCAL JUDGMENTS. It pulls the swarm's standing guidance
(a frame + its own echo) from GitHub raw, reconciles that guidance against local reality
using its OWN reasoning, decides, and reports telemetry append-only through its public
twin. Lose the link and it keeps thinking on its last *verified* echo — degrade-to-one.

  Guidance, not commands. The frame re-aims the edge; the edge does the thinking.

Actions (drop-in, stdlib only, no engine edit):
  sync    — fetch net/latest.json (cheap); if the tick advanced, pull+VERIFY the frame and
            this edge's echo, cache them. Offline? keep the last verified echo.
  judge   — the brainstem reasons: reconcile {frame directives + echo guidance} against the
            local `observations` you pass, and decide what to do now (uses the host LLM).
  report  — push telemetry (observations + judgment + outcome) append-only: to the local
            outbox always, and to the net via the GitHub Issues API when online + tokened.
  status  — tick, online/offline, last echo, last judgment, pending outbox.

Config (env): FRAME_NET_OWNER (kody-w), FRAME_NET_REPO (rapp-frame-net), FRAME_NODE_ID.
Read path = raw.githubusercontent.com (rapp-static-api). Write path = GitHub Issues (append-only).
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
_host_name = socket.gethostname().split(".")[0]
NODE_ID = os.environ.get("FRAME_NODE_ID", f"edge-{_host_name}")
RAW = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
HOME = os.path.expanduser("~/.brainstem/frame_net")  # the edge's memory of the net


def _brainstem():
    for nm in ("brainstem", "__main__"):
        m = sys.modules.get(nm)
        if m is not None and hasattr(m, "call_copilot"):
            return m
    return None


def _get(url, t=8):
    try:
        req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=t) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def _canon(d):
    """Canonical bytes of a frame/echo for hashing + signing (excludes volatile fields)."""
    return json.dumps({k: v for k, v in d.items() if k not in ("sig", "hash")},
                      sort_keys=True, separators=(",", ":"))


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
                "Make this brainstem an edge of the planetary frame-net (rapp-frame/1.0): pull the swarm's "
                "guidance (frame + echo) from GitHub, reconcile it with LOCAL reality by your own reasoning, "
                "act, and report telemetry append-only. Works offline on the last verified echo. "
                "action=sync (pull+verify the latest frame/echo), action=judge (reconcile guidance vs the "
                "`observations` you pass and decide), action=report (push telemetry), action=status."
            ),
            "parameters": {"type": "object", "properties": {
                "action": {"type": "string", "enum": ["sync", "judge", "report", "status"]},
                "observations": {"type": "string", "description": "for judge/report: what the edge is sensing locally right now"},
                "judgment": {"type": "string", "description": "for report: the decision the edge reached (from judge)"},
            }, "required": ["action"]},
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ---- sync: pull + verify the swarm's standing guidance ----
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
        latest_raw = _get(f"{RAW}/net/latest.json")
        if latest_raw is None:
            echo = _cache("echo.json")
            return json.dumps({"node": NODE_ID, "online": False, "using": "last verified echo" if echo else "none",
                               "tick": (_cache("latest.json") or {}).get("tick"),
                               "note": "offline — operating on the last verified echo (degrade-to-one)."})
        try:
            latest = json.loads(latest_raw)
        except Exception:
            return json.dumps({"node": NODE_ID, "online": True, "error": "latest.json not JSON (net not flocked?)"})
        prev = _cache("latest.json") or {}
        if latest.get("hash") and latest.get("hash") == prev.get("hash"):
            return json.dumps({"node": NODE_ID, "online": True, "new": False, "tick": latest.get("tick"),
                               "note": "nothing new — keep running on current echo."})
        # pull the frame + verify content-integrity (verify-before-act)
        frame_raw = _get(f"{RAW}/net/frames/{latest['hash']}.json")
        if frame_raw is None:
            return json.dumps({"node": NODE_ID, "online": True, "error": "could not fetch frame", "tick": latest.get("tick")})
        try:
            frame = json.loads(frame_raw)
        except Exception:
            return json.dumps({"node": NODE_ID, "online": True, "error": "frame not JSON — refusing to act"})
        if _sha16(_canon(frame)) != latest["hash"]:
            return json.dumps({"node": NODE_ID, "online": True, "verified": False,
                               "error": "frame hash mismatch — TAMPERED. Refusing to act; keeping last verified echo."})
        # pull this edge's echo from its public-twin inbox (fallback to net/echos)
        echo_raw = _get(f"{RAW}/twins/{NODE_ID}/inbox/latest.json") or _get(f"{RAW}/net/echos/{NODE_ID}.json")
        echo = None
        if echo_raw:
            try:
                echo = json.loads(echo_raw)
            except Exception:
                echo = None
        _cache("latest.json", latest)
        _cache("frame.json", frame)
        if echo is not None:
            _cache("echo.json", echo)
        return json.dumps({"node": NODE_ID, "online": True, "new": True, "verified": True, "tick": latest.get("tick"),
                           "directives": frame.get("directives", []),
                           "echo_guidance": (echo or {}).get("guidance", "(no echo yet — report telemetry to forge one)"),
                           "note": "guidance refreshed. Run action=judge with your local observations to decide."})

    # ---- judge: the brainstem reconciles guidance vs local reality ----
    def _judge(self, observations):
        frame = _cache("frame.json") or {}
        echo = _cache("echo.json") or {}
        directives = frame.get("directives", [])
        guidance = echo.get("guidance", "")
        bs = _brainstem()
        prompt = (
            "You are an edge brainstem on a high-latency, intermittent link to a swarm. You may be acting on "
            "guidance that is hours or days old, and you might be fully offline. The swarm's STANDING GUIDANCE:\n"
            f"  directives: {json.dumps(directives)}\n  your echo guidance: {guidance or '(none yet)'}\n\n"
            f"Your LOCAL observations right now:\n  {observations or '(none provided)'}\n\n"
            "The guidance is GUIDANCE, not a command. Reconcile it against what you are actually sensing locally and "
            "decide what to DO now. If guidance conflicts with local reality, local reality + your judgment win — and "
            "flag the conflict so it goes back to the swarm as telemetry. Be decisive but safe: if an action is "
            "destructive/irreversible and you are unsure or the guidance is stale, prefer to observe and report rather "
            "than act. Reply with: DECISION (one line), REASONING (2-3 lines), and CONFLICT (any guidance-vs-local conflict, or 'none')."
        )
        if bs is None:
            return json.dumps({"node": NODE_ID, "judgment": "(no host LLM reachable — cannot reason; staying in observe-and-report mode)",
                               "offline_reasoning": True})
        try:
            out = bs.call_copilot([{"role": "user", "content": prompt}])
            text = out[0] if isinstance(out, tuple) else out
            if isinstance(text, dict):
                text = (text.get("choices", [{}])[0].get("message", {}) or {}).get("content", str(text))
        except Exception as e:
            return json.dumps({"node": NODE_ID, "error": f"local judgment failed: {e}"})
        judgment = str(text).strip()
        _cache("last_judgment.json", {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "observations": observations, "judgment": judgment})
        return json.dumps({"node": NODE_ID, "tick": (frame or {}).get("tick"), "judgment": judgment,
                           "next": "run action=report to send this back to the swarm (forges your next echo)."})

    # ---- report: append-only telemetry up to the public twin / swarm ----
    def _report(self, observations, judgment):
        if not judgment:
            lj = _cache("last_judgment.json") or {}
            judgment = lj.get("judgment", "")
            observations = observations or lj.get("observations", "")
        tick = (_cache("frame.json") or {}).get("tick")
        telem = {"node": NODE_ID, "tick": tick, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "observations": observations, "judgment": judgment}
        # always buffer locally (the outbox survives a blackout)
        ob = os.path.join(HOME, "outbox")
        os.makedirs(ob, exist_ok=True)
        fname = f"{int(time.time())}.json"
        json.dump(telem, open(os.path.join(ob, fname), "w"), indent=2)
        # try to flush to the net via the GitHub Issues API (append-only)
        via, posted = "outbox (buffered — offline/no token)", False
        tok = _github_token()
        if tok:
            try:
                body = json.dumps({"title": f"telemetry: {NODE_ID} tick {tick}",
                                   "body": "```json\n" + json.dumps(telem, indent=2) + "\n```",
                                   "labels": ["telemetry", NODE_ID]}).encode()
                req = urllib.request.Request(f"{API}/issues", data=body, method="POST",
                                             headers={"Authorization": f"Bearer {tok}",
                                                      "Accept": "application/vnd.github+json",
                                                      "User-Agent": "rapp-frame-edge"})
                with urllib.request.urlopen(req, timeout=12) as r:
                    num = json.loads(r.read()).get("number")
                via, posted = f"GitHub issue #{num} (append-only)", True
                os.remove(os.path.join(ob, fname))
            except Exception as e:
                via = f"outbox (issue post failed: {str(e)[:80]})"
        return json.dumps({"node": NODE_ID, "reported": True, "posted_to_net": posted, "via": via,
                           "note": "telemetry banked; the swarm forges your next echo from it."})

    def _status(self):
        latest = _cache("latest.json") or {}
        echo = _cache("echo.json") or {}
        lj = _cache("last_judgment.json") or {}
        pending = len(os.listdir(os.path.join(HOME, "outbox"))) if os.path.isdir(os.path.join(HOME, "outbox")) else 0
        online = _get(f"{RAW}/net/latest.json", t=5) is not None
        return json.dumps({"node": NODE_ID, "net": f"{OWNER}/{REPO}", "online": online,
                           "tick": latest.get("tick"), "echo_guidance": echo.get("guidance", "(none)"),
                           "last_judgment_at": lj.get("at"), "pending_telemetry": pending}, indent=2)
