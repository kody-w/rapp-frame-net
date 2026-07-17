# rapp-frame-net — retired, read-only evidence

This repository is **not an active RAPP wire**. Its former `rapp-frame/2.0`
producer, consumer, GitHub Issues write path, and forge workflow were retired
because they cannot satisfy RAPP/1 without an authenticated registry and
estate-owner signing authority.

The only current protocol authority is:

- `kody-w/rapp-1`
- commit `6723c7add2aed36bb68992fc71a56b0a4bd5ad81`
- `SPEC.md` SHA-256
  `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b`

See [AUTHORITY.md](AUTHORITY.md) for the compliance decision, RAPP/1 floor,
security findings, and owner-only recovery actions.

## What remains

Committed JSON under `events/`, `net/frames/`, `twins/`, `views/`, and
`keys/verify.json` is preserved byte-for-byte as historical evidence. It uses
obsolete envelopes and trust claims. It is **UNVERIFIED**, is not active
authority, and must not be repaired, reparented, rehashed, resigned,
regenerated, or deleted. Exact baseline blob and SHA-256 pins are in
[`audit/immutable-evidence.json`](audit/immutable-evidence.json).

The mutable legacy head `net/latest.json` was removed from the current tree so
the former polling URL is non-actionable after merge. Its exact bytes remain
available at the pinned baseline commit; no historical ref was rewritten.

## Fail-closed paths

- `edge_node_agent.py` is an offline tombstone and performs no fetch, action,
  `/chat` integration, or GitHub write.
- `scripts/event_store.py` and `scripts/frame_loop.py` are offline tombstones
  and perform no mutation or materialization.
- `.github/workflows/forge.yml` has no permissions and its only job is
  unconditionally skipped. It has no schedule, Issues trigger, write grant, or
  third-party action.

Source containment cannot stop already-deployed copies. Token revocation,
agent/process and scheduler shutdown, Issues-plane closure, repository
metadata and mirror/CDN retirement, cache invalidation, and consumer migration
are explicit owner/external gates in
[`audit/owner-decommission-inputs.json`](audit/owner-decommission-inputs.json).
Every owner input is deliberately `null`; operational decommission acceptance
is therefore **BLOCKED**, not assumed.

Every tracked path is classified in
[`audit/tracked-path-classification.json`](audit/tracked-path-classification.json);
tests reject unclassified additions.

There is no installer in this repository, and this retirement adds none.
