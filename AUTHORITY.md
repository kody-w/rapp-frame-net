# Authority and retirement status

## Authority

| item | pinned value |
|---|---|
| canonical repository | `kody-w/rapp-1` |
| commit | `6723c7add2aed36bb68992fc71a56b0a4bd5ad81` |
| normative path | `SPEC.md` |
| file SHA-256 | `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b` |
| revision | RAPP/1 rev-5 |

The local former `rapp-frame/2.0` specification is retired. It and older
`rapp-frame/1.0` forms have no current authority.

## Status

**The current checkout is retired and fail-closed: it has no active producer,
consumer, launcher, workflow job, head pointer, mirror client, or wire
adapter. Operational decommission of previously deployed copies is not yet
owner-attested.**

No target-owned RAPP/1 adapter was created. A swarm frame must be signed, and
signature verification depends on the authenticated, monotonic §13 registry.
This repository contains neither an authenticated registry nor estate-owner
signing authority. Minting keys, signatures, registry entries, genesis,
re-genesis, tombstones, or trust declarations would be fabrication.

All preserved historical artifacts are **UNVERIFIED**. A matching legacy
content hash proves only consistency with the obsolete encoding; it does not
authenticate the producer, current head, kind, genesis, key, or owner. Any
signature-bearing artifact also remains **UNVERIFIED** unless it is checked
against an authenticated, fresh §13 registry.

## RAPP/1 floor applied

The audit checked the following normative floor:

1. A frame has exactly the eleven keys `spec`, `kind`, `stream_id`, `seq`,
   `utc`, `payload`, `payload_hash`, `frame_hash`, `prev`, `prev_wave`, and
   `sig`; `spec` is exactly `rapp/1`.
2. Canonical bytes are RFC 8785 JCS over the restricted I-JSON input domain.
   Duplicate names, lone surrogates, non-round-tripping/non-finite numbers,
   excessive depth, and excessive size are refused rather than repaired.
3. `payload_hash = H("rapp/1:particle", payload)` and
   `frame_hash = H("rapp/1:wave", frame minus frame_hash and sig)`, where
   `H(space,v) = SHA-256(UTF8(space) || LF || canonical(v))`. Hashes are full
   lowercase 64-hex and stores separate address spaces.
4. Kinds and their stream families are exact §13 registry bindings, not
   prefix inference. Every stream has one current registered genesis.
5. Consumers bind the stream, enforce particle and wave links, contiguous
   sequence and time, persist the highest verified head, reject rollback, and
   stop both branches at a fork. They never repair or reparent evidence.
6. Swarm frames require a valid detached JWS and authenticated §13 key,
   owner-tenure, re-anchor, and tombstone resolution. Without that registry,
   the only correct result is **UNVERIFIED/refused**.
7. The synchronous wire is only `POST /chat`; this repository implements no
   `/chat` service. A conformant request requires `user_input`, permits only
   optional `session_id`/`idempotency_key` semantics, and ignores unknown
   members. Success has exactly `{response, agent_logs, session_id}`; refusal
   is HTTP 422 with exactly `{error:{code,step}}`. New capability cannot be
   exposed as a sibling route.
8. The asynchronous wire is a conformant append-only RAPP/1 frame, not a
   GitHub Issue body or the retired event envelope.

## Findings and containment

| surface | finding | containment |
|---|---|---|
| guidance and echo JSON | obsolete 8/10-key `rapp-frame/2.0` envelopes; untagged hashes; no `sig` | preserved byte-for-byte, classified UNVERIFIED, never served as current by target code |
| `keys/verify.json` | legacy prose, null public key, no authenticated §13 registry | preserved as evidence; never treated as a trust source |
| edge consumer | accepted partial/truncated hashes, skipped exact shape, registry, signatures, chain, fork, head rollback, and echo verification | replaced by an offline refusal tombstone |
| network | arbitrary `FRAME_HEADS` plus moving `main` URLs allowed SSRF/local-resource access and stale/forked heads | all target network access removed |
| telemetry | observations/judgments could be posted publicly through Issues without protocol validation or secret classification | Issues write path removed; no token is read |
| forge | public Issues could trigger ingest; workflow had broad content/issue writes and an unpinned action tag | triggers/writes/actions removed; sole job is unconditionally skipped with no permissions |
| materializer/store | rewrote committed state and used a non-RAPP event schema; locking did not protect the replacement inode | both paths replaced by offline refusal tombstones |
| transport docs | treated content hashes and interchangeable moving heads as trust | replaced with historical status and RAPP/1 head/registry requirements |

No active code follows a moving branch, accepts a caller-provided URL, performs
network I/O, reads a secret, writes an Issue, or mutates repository state.

## Current live-path containment

- The mutable legacy pointer `net/latest.json` is deleted from the current
  tree. A merged raw/CDN request eventually returns not-found rather than a
  guidance head. The exact prior blob remains at baseline
  `a78a9c2aba06f9e788d735341b9ff7d2cace3189:net/latest.json`.
- The three former Python entry points are refusal tombstones.
- The workflow has no permissions and an unconditionally false job.
- Immutable event/frame/twin/key/view blobs remain in place as evidence. They
  are not edited merely because their historical paths resemble APIs.

Deleting the mutable pointer cannot stop an old agent already running on a
cached echo; that behavior was an explicit legacy feature. CDN caches, forks,
mirrors, installed files, local schedulers, credentials, repository settings,
and third-party consumers are also outside this Git tree. They are owner or
operator decommission responsibilities, not facts this commit may invent.

## Immutable evidence

The byte-level inventory is
[`audit/immutable-evidence.json`](audit/immutable-evidence.json). It pins the
baseline commit, Git blob IDs, and SHA-256 of every immutable event, frame,
twin state/inbox/identity, key record, and materialized view. Tests resolve the
hardcoded baseline independently, read each baseline blob, compare its bytes
and IDs with both the manifest and current bytes, and fail if a blob and
manifest are changed together.

These locations are evidence, not APIs:

- `events/frame-1.json`
- `net/frames/`
- `twins/`
- `keys/verify.json`
- `views/events.json`

The former mutable `net/latest.json` pointer is retained only through the
pinned historical commit and is listed separately in both audit inventories.

## Operational decommission acceptance — currently blocked

The exact public-safe input contract is
[`audit/owner-decommission-inputs.json`](audit/owner-decommission-inputs.json).
All inputs are intentionally `null`; `null` never means success. An owner or
responsible external operator must supply reviewed evidence for every gate:

1. revoke every legacy GitHub/deploy/personal token and credential;
2. stop installed legacy agent processes and disable every external scheduler;
3. disable or otherwise close the repository Issues write plane and drain or
   close legacy telemetry submissions as policy permits;
4. mark repository description/homepage/topics as retired and remove live
   endpoint claims;
5. retire live mirrors and CDN advertisements and invalidate cached
   `net/latest.json` where the provider supports it;
6. migrate every known consumer to an explicitly named, reviewed path (or
   record removal), then provide migration acceptance evidence; and
7. record final owner decommission acceptance.

No token value, private key, credential, or private operational detail belongs
in the input file—only public-safe evidence references and timestamps.

Local acceptance tests prove checkout containment, baseline preservation,
co-tamper rejection, exact path classification, and the null-input block. They
cannot prove external actions. Merge readiness for code and operational
decommission acceptance are distinct.

## Estate-owner actions required for any future activation

1. Publish and authenticate the §13 registry from its canonical source,
   including the out-of-band estate-owner anchor, monotonic `registry_seq`,
   registered protocol/kinds/genesis, SPKI entries, and applicable succession
   or tombstone records.
2. Decide whether this stream should remain retired. If convergence is
   desired, perform the owner-authorized §12.1 operation outside this audit;
   do not patch, reparent, rehash, or resign the retained artifacts.
3. Provide owner-controlled signing through a reviewed secret boundary. Never
   place a private key or token in this public repository, logs, frames,
   Issues, workflow arguments, or generated handoff.
4. Implement and independently test the complete §7.5 verifier, §7.6
   fork/head persistence, registry rollback/freshness policy, fixed-origin
   network allowlist, bounded I/O, and secret redaction before enabling a
   producer or consumer.
5. Publish immutable commit/hash-pinned endpoints and provenance-stamped
   mirrors. A moving `main` URL must not be a trust decision.

Until all owner actions are complete, fail-closed retirement is the only
authorized behavior.
