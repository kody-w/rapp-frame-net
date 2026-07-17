# Historical note: the retired “Hydra” transport

This file formerly described a multi-head `rapp-frame/2.0` transport that read
from moving `main` branches and user-supplied URLs. That design is historical,
not active authority.

RAPP/1 does not make an arbitrary mirror or a content hash a trust root:

- history is safe only given a trusted, authenticated head;
- consumers must enforce monotonic heads and fail closed on forks;
- swarm frames require signatures;
- kinds, genesis, keys, revocations, and owner tenure resolve through the
  authenticated, rollback-protected §13 registry; and
- mirrors must be provenance-stamped and subordinate to the canonical source.

The retired edge accepted arbitrary `FRAME_HEADS`, creating an SSRF/local
resource risk, and defaulted to unpinned moving `main` URLs. Those network paths
have been removed. No mirror, CDN, IPFS gateway, or branch URL named in
repository history is currently trusted by this repository.

The mutable current head path `net/latest.json` is absent from this tree. Its
historical bytes remain at baseline
`a78a9c2aba06f9e788d735341b9ff7d2cace3189`; that ref must not be rewritten.
Previously deployed agents and cached/mirrored copies are outside this
checkout. The owner must stop those processes, retire advertisements and
mirrors, and invalidate caches before operational decommission can be
accepted. Those attestations are currently `null`.

Historical data remains byte-for-byte evidence and **UNVERIFIED**. See
[AUTHORITY.md](AUTHORITY.md) and
[`audit/immutable-evidence.json`](audit/immutable-evidence.json).
