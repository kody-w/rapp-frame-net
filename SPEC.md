# Retired local specification

The former `rapp-frame/2.0` text in this repository is obsolete historical
documentation. It is not a protocol specification of record and must not be
used to produce or accept frames.

The sole normative authority for this audit is `kody-w/rapp-1` at commit
`6723c7add2aed36bb68992fc71a56b0a4bd5ad81`, whose `SPEC.md` has SHA-256
`6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b`.
That RAPP/1 rev-5 authority obsoletes `rapp-frame/1.0` and
`rapp-frame/2.0`.

No RAPP/1 adapter is emitted here. A conformant swarm producer would require,
among other things, the exact eleven-key `rapp/1` frame, RFC 8785 JCS over
I-JSON, domain-separated particle and wave hashes, a registered kind and
genesis, chain/head/fork enforcement, an authenticated §13 registry, and a
valid owner-authorized signature. This repository has neither authenticated
registry material nor owner signing authority; inventing either would be a
trust forgery.

The old JSON artifacts remain immutable, **UNVERIFIED** evidence. Current
status, exact requirements checked, and owner-only actions are documented in
[AUTHORITY.md](AUTHORITY.md).
