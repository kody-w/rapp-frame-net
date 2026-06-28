# rapp-frame/2.0 — the unified frame: memory mutations *and* the planetary swarm wire

> **2.0 unifies two things that were the same animal all along.** The kernel already ships
> `rapp-frame/1.0` — the Dream-Catcher **memory-mutation** event ([RAPP/ECOSYSTEM.md §147](https://github.com/kody-w/RAPP/blob/main/ECOSYSTEM.md), tested 17/17): a content-addressed,
> hash-chained, UTC-first append-only log of an organism's life. This repo originally minted a
> *second, colliding* `rapp-frame/1.0` for the planetary swarm wire — a different object under the
> same id. **2.0 resolves the collision by making them one family.** A frame is a frame; `kind`
> says whether it's a memory mutation or a swarm signal. Every kernel `rapp-frame/1.0` frame is a
> valid `rapp-frame/2.0` frame; 2.0 only *adds* the swarm kinds, pins the canonical hash, and makes
> the signature optional. **No kernel edit** — the kernel adopts 2.0 by widening its `kind` set when ready.

## The unified envelope

```json
{
  "spec":      "rapp-frame/2.0",
  "stream_id": "<stream>",          // memory: "<rappid>:<instance>"  ·  swarm: "net:<name>"
  "frame_n":   1,                   // integer, monotonic per stream
  "utc":       "<iso8601>",         // UTC-first canon
  "kind":      "<kind>",            // memory.* | swarm.* (see kinds)
  "payload":   { },                 // kind-specific body
  "prev_hash": null,                // sha256 of the previous frame in this stream (null at genesis)
  "hash":      "<sha256>",          // content address — see Hashing
  "sig":       "<optional>"         // OPTIONAL authenticity (see Trust)
}
```

The **slug is the name; the hash is the identity** — `frame_n`/`utc` order the stream, `hash`
content-addresses the frame, `prev_hash` chains it. Frames are **never mutated**: a new state is a
new frame at a new hash, and the stream's pointer re-points.

## The two kind families (one envelope)

| family | `kind` values | `stream_id` | what it logs |
|---|---|---|---|
| **memory** (the kernel's original 1.0) | `memory.chat-turn` · `memory.tool-call` · `memory.save` · `resurrection` · … | `<rappid>:<instance>` | one organism's life — the Dream-Catcher mutation log (`data/frames.json`, doorman `appendFrame()`) |
| **swarm** (the planetary wire) | `swarm.guidance` · `swarm.echo` · `swarm.telemetry` | `net:<name>` | the swarm's standing word, per-edge echos, and edge telemetry |

> Backwards-compat: a kernel 1.0 frame `{stream_id, frame_n, utc, kind, payload, prev_hash, hash}`
> *is* a 2.0 frame — its `kind` simply falls in the memory family. Legacy bare kinds (`chat-turn`)
> are read as `memory.chat-turn`. We **read every legacy form, emit only canonical** — identity is
> the hash, never the spec string (the [rapp compatibility contract](https://github.com/kody-w/RAPP)).

## Hashing (pinned in 2.0)

```
canonical(frame) = json(frame without "hash" and "sig", keys sorted, no whitespace)
hash             = sha256( canonical(frame) )        # full 64-hex, never truncated
```

Full SHA-256 (2.0 fixes the swarm wire's old `[:16]` truncation) — 2^128 birthday resistance, the
same width the kernel's memory frames and `rappid` eternity use. The CDN (or a hostile mirror)
**cannot tamper without breaking the hash**, which is why any head is safe to read from (see HYDRA).

## UTC-first canon + the Dream Catcher (works on any stream)

Because memory and swarm frames share one envelope, the kernel's **Dream-Catcher reassimilation**
([ECOSYSTEM §15](https://github.com/kody-w/RAPP/blob/main/ECOSYSTEM.md)) now works on *swarm* streams too:

- **UTC-first:** whichever frame hit the UTC first is canonical.
- **Non-contradicting** later frames layer on.
- **Contradicting** frames (same `(utc, frame_n)` PK, different content) are **preserved as
  alternate-dimension data, not lost** — and a frame-diff-by-hash surfaces them for a PR reassimilation.

An offline edge living on its last echo is exactly a *parallel dimension*; when it reconnects, its
buffered telemetry frames reassimilate by the same UTC-first rule. The swarm wire *is* the Dream
Catcher, run across machines instead of across re-hatches.

## Transport — GitHub as a free, global, serverless data layer

| direction | mechanism | why |
|---|---|---|
| **READ** (frames, echos) | `raw.githubusercontent.com/<owner>/<net>/main/...` | CDN-cached, CORS-open, no auth, cheap to poll over a bad link (`rapp-static-api/1.0`) |
| **WRITE** (telemetry) | **GitHub Issues API** — open an issue / comment | append-only by nature; attributed; auditable; needs only a token |

No server. The network is a public repo; compute on the global side is a **GitHub Action** (the
frame foundry). Reads are free and global; writes are append-only events.

## The swarm objects

### `net/latest.json` — the heartbeat pointer (poll this; it's tiny)
```json
{ "spec": "rapp-frame/2.0", "stream_id": "net:<name>", "frame_n": 1041, "kind": "swarm.guidance",
  "hash": "<sha256>", "utc": "...", "frame": "net/frames/<sha256>.json" }
```
`frame_n` is the swarm's clock (one frame per period — a "sol"). An edge fetches `latest.json`
first; if `hash` is unchanged, there is nothing new and it keeps running on what it has.

### `net/frames/<hash>.json` — a `swarm.guidance` frame (the swarm's standing word)
```json
{ "spec": "rapp-frame/2.0", "stream_id": "net:<name>", "frame_n": 1041, "utc": "...",
  "kind": "swarm.guidance", "prev_hash": "<prev>",
  "payload": { "directives": [ "report your capability inventory", "converge objective: <X>" ],
               "world": { "...shared state every edge can see..." } },
  "hash": "<sha256>" }
```

### `net/echos/<node-id>.json` (or `twins/<node-id>/inbox/`) — a `swarm.echo` frame (forged *for one edge*)
```json
{ "spec": "rapp-frame/2.0", "stream_id": "net:<name>", "frame_n": 1041, "utc": "...",
  "kind": "swarm.echo", "for": "<node-id>", "ack": "<telemetry id this echo answers>",
  "payload": { "guidance": "given what you reported, here is your aim until next contact",
               "constraints": [ "..." ] },
  "hash": "<sha256>" }
```
The **echo is the load-bearing primitive** — computed *from the edge's last telemetry*. Between
contacts the edge runs on its echo + local reality. This is **the Foundry inverted**: instead of
manufacturing capability and pushing it fleet-wide, the global side manufactures *echos* from
returned telemetry and serves them via raw.

## The edge loop (the edge is a brainstem)

```
every tick (or every /chat, or on a timer):
  1. SENSE     GET net/latest.json.  Unchanged hash or no network? -> keep last echo, skip to 4.
  2. PULL      GET frames/<hash>.json + the inbox echo.  VERIFY before use (below).
  3. RE-AIM    cache them as the new standing guidance.
  4. JUDGE     the BRAINSTEM reasons: reconcile {payload.directives, echo guidance} against
               local telemetry + state, and decide what to do now. Guidance != command.
  5. ACT       run local agents on that judgment.
  6. REPORT    on next contact, push a swarm.telemetry frame (what I saw/judged/did) as an
               append-only GitHub Issue. That telemetry forges my next echo.
```
**Degrade-to-one:** steps 1–2 may fail (blackout). The edge proceeds from its cached echo and local
judgment indefinitely. One brainstem, no network, still useful. Reconnect → re-aim on the newest
frame and flush buffered telemetry (which reassimilates UTC-first).

## The edge's public twin — a stable front door (async mailbox)

A live edge is intermittent; its **public twin is not.** Every edge has an always-reachable presence
on GitHub — the ecosystem's existing *"a public repo is a front door to a twin"* pattern
([rapp-vneighborhood](https://github.com/kody-w/rapp-vneighborhood), `kody-twin`, the planted twins):

```
twins/<node-id>/twin.json      rappid identity (who this edge is)
twins/<node-id>/state.json     last-known state (read this when the edge is dark)
twins/<node-id>/inbox/         the MAILBOX — swarm.echo frames + messages addressed to this edge
twins/<node-id>/outbox/        swarm.telemetry frames the edge has flushed (append-only)
```

Other nodes address the edge **through its twin, not its live connection** — read its last-known
`state.json`, drop into its `inbox/`. When the edge next has signal it **drains its inbox**, **publishes
fresh state**, **flushes its outbox**, then returns to local judgment. The twin is the stable identity
and async mailbox; the live brainstem is the body that animates it on contact.

## Trust — verify before you act

1. **Integrity (ALWAYS — this is the trust root):** recompute `sha256(canonical(frame))`; it MUST
   equal the `hash` in the pointer and the filename. Content-addressing is the trust; a tampered head
   breaks the hash. **An edge that cannot hash-verify a frame does not act on it** — it keeps its last
   verified echo.
2. **Authorship (DEFAULT — gh-collaborator):** who may advance a net's frames is **GitHub-collaborator
   status** on the net repo (the canonical RAPP trust model — [MASTER_PLAN](https://github.com/kody-w/RAPP/blob/main/MASTER_PLAN.md) Part Deux §3,
   *"gh collaborator IS the auth, no separate PKI"*). PR-consent gates what lands. No keys to manage.
3. **Authenticity (OPTIONAL — opt-in sovereignty):** a net MAY carry a `sig` over `canonical(frame)`
   so frames verify against a public key alone (surviving a host takedown) — the frame-level analog of
   [rappid eternity's optional keypair](https://github.com/kody-w/RAPP). This is **never required**: it
   is an opt-in attestation for nets that want platform-independent authorship, exactly as the rest of
   the estate keeps signing optional over a gh-collaborator default. The content-hash, not the sig, is
   what every edge checks.

## The frame foundry (global side, serverless)

A GitHub Action (`forge`) on the net repo: ingest new telemetry (Issues since last tick) → forge each
edge's next `swarm.echo` (deterministic policy, or a coordinating brainstem that reasons over the
telemetry) → commit new frames/echos → advance `latest.json`. The clock can be a cron (one tick per
period) or telemetry-driven.

## How it composes

- Same organism as the **Leviathan Protocol** ([kody-w/leviathan](https://github.com/kody-w/leviathan)) — one mind, many bodies — but async. Near bodies: the sync wire. Far/intermittent bodies: this frame wire.
- One **frame** envelope, two kind families: the kernel's **memory** mutations + the **swarm** wire — reassimilated by the same Dream-Catcher, UTC-first.
- Read primitive = `rapp-static-api/1.0`; write primitive = GitHub Issues; survival = `rapp-hydra` (many heads); seal = `rapp-sealed` (private nets are ciphertext, equally mirrored).
- Routable from [rapp-spine](https://github.com/kody-w/rapp-spine): *"a brainstem on a spotty/high-latency link must act autonomously and re-aim when it can reach the swarm"* → **rapp-frame/2.0** (`kind: swarm.*`).

---

*One frame for the organism's memory and for the swarm's word — content-addressed, UTC-first,
verified before acting. Cells all the way down, bodies all the way out, light-minutes apart.*
