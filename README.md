# 🛰️ rapp-frame-net — the planetary swarm wire

**The Leviathan, async.** The LAN Leviathan drives many brainstem *bodies* as one mind over a
synchronous wire. **rapp-frame** is the same organism over the opposite wire — an **append-only
frame/echo log served from GitHub** — for edges that are far apart, on intermittent links, and
seconds-to-days of light-delay away. *A brainstem on Mars.*

> The rule that makes it work: **the edge is a brainstem. It makes local judgments.** A frame is
> the swarm's standing *guidance*, never a command queue. The edge reconciles the last frame it
> got against what it's sensing *now*, with its own reasoning, and acts. Drop the link entirely
> and a single edge keeps working on its last verified echo. Full spec: **[SPEC.md](SPEC.md)**.

## The wire is GitHub (no server, global, free, auditable)

| direction | mechanism |
|---|---|
| **READ** frames + echos | `raw.githubusercontent.com/.../main/...` (CDN, CORS-open — `rapp-static-api/1.0`) |
| **WRITE** telemetry | the **GitHub Issues API** (append-only, attributed) |
| **forge** (global compute) | a **GitHub Action** ([`forge.py`](forge.py)) — no server anywhere |

## The objects

- **[`net/latest.json`](net/latest.json)** — the heartbeat pointer `{tick, hash}` (poll this; it's tiny).
- **`net/frames/<hash>.json`** — content-addressed, append-only frames (the swarm's standing word).
- **`twins/<node>/`** — each edge's **public twin**: an always-reachable front door — `twin.json`
  (identity + verify key), `state.json` (last-known state), `inbox/` (its echo + messages), `outbox/`
  (flushed telemetry). Others reach the edge *through its twin*, not its live link.

## The edge loop

```
SENSE  GET latest.json   (unchanged hash or offline? -> keep last echo)
PULL   GET the frame + my echo, VERIFY (sha256 content-address) before use
JUDGE  the brainstem reconciles {directives + echo guidance} vs local reality -> decides
ACT    run local agents on that judgment
REPORT push telemetry append-only (GitHub Issue) -> the forge forges my next echo
```
**Degrade-to-one:** a single offline brainstem keeps thinking on its last verified echo. Reconnect →
re-aim on the newest frame, flush buffered telemetry.

## Run an edge in 30 seconds

Drop [`edge_node_agent.py`](https://raw.githubusercontent.com/kody-w/rapp-frame-net/main/edge_node_agent.py)
into any brainstem's `agents/`, then:
```bash
# pull the swarm's guidance and verify it
curl -s localhost:7071/api/agent/EdgeNode -d '{"action":"sync"}'
# the brainstem reconciles guidance vs what it's seeing locally and decides
curl -s localhost:7071/api/agent/EdgeNode -d '{"action":"judge","observations":"disk 12% free; one agent erroring"}'
# report it back (append-only) -> forges your next echo
curl -s localhost:7071/api/agent/EdgeNode -d '{"action":"report"}'
```

## Verify before you act

Every frame is content-addressed: `sha256(canonical(frame))[:16] == latest.json.hash == filename`.
An edge recomputes it and **refuses to act on a mismatch.** v1.0 ships this content root + an HMAC
profile; the production authenticity layer is **Ed25519 / `rapp-moment` ECDSA P-256** (edges verify
with a public key alone). See [`keys/verify.json`](keys/verify.json) and [SPEC §Verification](SPEC.md).

## Where it sits

Same organism as the **[Leviathan Protocol](https://github.com/kody-w/leviathan)** (one mind, many
bodies) — near bodies: the sync wire; far/intermittent: this frame wire. Read primitive =
[`rapp-static-api/1.0`](https://github.com/kody-w/rapp-static-apis); identity/seal = `rapp-moment` /
`rapp-sealed`; routed by **[rapp-spine](https://github.com/kody-w/rapp-spine)**; locked into the
[Foundation](https://github.com/kody-w/rapp-spine/blob/main/FOUNDATION.md). The kernel never changes —
an edge is a full brainstem, so **every RAPP hero use case works at the edge, unchanged.**

---

*Frames re-aim the edge; the edge does the thinking. Cells all the way down, bodies all the way out — now light-minutes apart.*

> ⚠️ Security: telemetry is public, and an edge runs real agents. Treat the net as **public + signed**;
> never put secrets in frames/telemetry; the adversarial backlog (in [rapp-roadmap](https://github.com/kody-w/rapp-roadmap)) tracks the hardening path.
