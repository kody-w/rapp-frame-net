# rapp-frame/1.0 — the planetary swarm wire

The LAN Leviathan drives many brainstem **bodies** as one mind over a synchronous wire
(`POST /api/agent`). **rapp-frame** is the same organism over the *opposite* wire: an
**append-only frame/echo log served from GitHub**, for edges that are far away, on
intermittent links, and seconds-to-days of light-delay apart — *a brainstem on Mars.*

The defining rule: **the edge is a brainstem. It makes local judgments.** A frame is the
swarm's standing *guidance*, never a command queue. The edge reconciles the last frame it
received against what it is encountering locally — with its own reasoning — and acts. It
needs the network only to occasionally **re-aim** it, not to think for it. Drop the link
entirely and a single edge brainstem keeps working on its last echo.

## Transport — GitHub as a free, global, serverless data layer

| direction | mechanism | why |
|---|---|---|
| **READ** (frames, echos) | `raw.githubusercontent.com/<owner>/<net>/main/...` | CDN-cached, CORS-open, no auth, cheap to poll over a bad link (this is `rapp-static-api/1.0`) |
| **WRITE** (telemetry) | **GitHub Issues API** — open an issue / comment | append-only by nature; attributed; auditable; needs only a token |

No server. The whole network is a public repo. Compute on the global side is a **GitHub
Action** (the frame foundry). Reads are free and global; writes are append-only events.

## The three objects

### `net/latest.json` — the heartbeat pointer (poll this; it's tiny)
```json
{ "spec": "rapp-frame/1.0", "net": "<name>", "tick": 1041, "hash": "73a37195f3e293ec",
  "updated": "2026-06-28T08:49:54Z", "frame": "frames/73a37195f3e293ec.json" }
```
`tick` is the swarm's clock (one frame per period — a "sol"). `hash` is the content address
of the current frame. An edge fetches `latest.json` first; if `hash` is unchanged, there is
nothing new and it keeps running on what it has.

### `net/frames/<hash>.json` — a frame (the swarm's standing word, append-only chain)
```json
{ "spec": "rapp-frame/1.0", "tick": 1041, "updated": "...", "prev": "<prev-hash>",
  "directives": [ "report your capability inventory", "converge objective: <X>" ],
  "world": { "...shared state every edge can see..." },
  "sig": "<authenticity signature — see Verification>" }
```
Content-addressed: the filename **is** `sha256(canonical(frame_without_hash))[:16]`. Frames
chain by `prev` into an append-only history. Frames are **never mutated** — a new state is a
new frame at a new hash, and `latest.json` re-points.

### `net/echos/<node-id>.json` — an echo (guidance forged *for one edge*)
```json
{ "spec": "rapp-frame-echo/1.0", "for": "<node-id>", "tick": 1041,
  "ack": "<id of the telemetry this echo answers>",
  "guidance": "given what you reported, here is your standing aim until next contact",
  "constraints": [ "..." ], "updated": "...", "sig": "..." }
```
The **echo is the load-bearing primitive.** It is computed *from the edge's last telemetry*:
"here's your aim until I hear from you again." Between contacts the edge runs on its echo +
local reality. This is **the Foundry inverted** — instead of manufacturing capability and
pushing it fleet-wide, the global side manufactures *echos* from returned telemetry and
serves them via raw.

## The edge loop (the edge is a brainstem)

```
every tick (or every /chat, or on a timer):
  1. SENSE     GET net/latest.json.  Unchanged hash or no network? -> keep last echo, skip to 4.
  2. PULL      GET frames/<hash>.json + echos/<me>.json.  VERIFY before use (below).
  3. RE-AIM    cache them as the new standing guidance.
  4. JUDGE     the BRAINSTEM reasons: reconcile {frame.directives, echo.guidance} against
               local telemetry + state, and decide what to do now. Guidance != command.
  5. ACT       run local agents on that judgment.
  6. REPORT    on next contact, push telemetry (what I saw, judged, did, outcomes) as an
               append-only GitHub Issue. That telemetry forges my next echo.
```
**Degrade-to-one:** steps 1–2 may fail (blackout). The edge proceeds from its cached echo
and local judgment indefinitely. One brainstem, no network, still useful. Reconnect and it
re-aims on the newest frame and flushes its buffered telemetry.

## The edge's public twin — a stable front door (async mailbox)

A live edge is intermittent; its **public twin is not.** Every edge has an always-reachable
presence on GitHub — the ecosystem's existing *"a public repo is a front door to a twin"*
pattern ([rapp-vneighborhood](https://github.com/kody-w/rapp-vneighborhood), `kody-twin`, the
planted twins) — reachable even when the edge is dark:

```
twins/<node-id>/twin.json      rappid identity + verify key (who this edge is)
twins/<node-id>/state.json     last-known state (read this when the edge is offline)
twins/<node-id>/inbox/         the MAILBOX — echos + messages addressed to this edge
twins/<node-id>/outbox/        telemetry the edge has flushed (append-only)
```

Other nodes address the edge **through its twin, not its live connection** — they read its
last-known `state.json` and drop into its `inbox/`. When the edge next has signal it **drains
its inbox** (collecting its newest echo + messages), **publishes fresh state**, and **flushes
its outbox**, then returns to local judgment. The twin is the stable identity and async
mailbox; the live brainstem is the body that animates it on contact. The unified Leviathan
once more: the twin is the BEING's front door, the live brainstem is the body, the swarm is
the fleet — now with a mailbox so absence isn't disconnection.

## Verification — verify before you act

1. **Integrity (always):** recompute `sha256(canonical(frame))[:16]`; it MUST equal the hash
   in `latest.json` and the filename. The CDN cannot tamper without breaking the hash.
2. **Authenticity (recommended):** `latest.json`, frames, and echos carry a `sig` over their
   canonical bytes. v1.0 ships an HMAC-SHA256 profile (shared net-secret) for closed nets; the
   production profile is **Ed25519 / `rapp-moment` ECDSA P-256** so edges verify with a public
   key alone and cannot forge. The verify key lives at `net/keys/verify.json`. An edge that
   cannot verify a frame **does not act on it** — it keeps its last verified echo.

## The frame foundry (global side, serverless)

A GitHub Action (`forge`) on the net repo: ingest new telemetry (Issues since last tick) ->
forge each edge's next echo (deterministic policy, or an LLM/coordinating-brainstem that
reasons about the telemetry) -> sign -> commit new frames/echos -> advance `latest.json`.
The clock can be a cron (one tick per period) or telemetry-driven.

## How it composes

- Same organism as the **Leviathan Protocol** ([kody-w/leviathan](https://github.com/kody-w/leviathan)) — one mind, many bodies — but async. Near bodies: the sync wire. Far/intermittent bodies: this frame wire.
- Read primitive = `rapp-static-api/1.0`; write primitive = GitHub Issues; identity/seal = `rapp-moment` / `rapp-sealed`.
- Routable from [rapp-spine](https://github.com/kody-w/rapp-spine): situation *"a brainstem on a spotty/high-latency link must act autonomously and re-aim when it can reach the swarm"* → **rapp-frame/1.0**.

---

*Frames re-aim the edge; the edge does the thinking. Cells all the way down, bodies all the way out, and now — light-minutes apart.*
