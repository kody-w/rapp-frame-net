# rapp-hydra/1.0 — the many-headed, unkillable medium

The protocol that makes the RAPP medium impossible to shut down. The swarm's entire state is
**static data in a git repo**, mirrored to **many independent heads** (CDNs, git hosts, IPFS,
forks). An edge reads from whichever head is reachable, and **trusts the data, not the host** —
every artifact is content-addressed, so a hostile or stale mirror can't tamper. Cut one head,
another serves it. Fork it, a new head grows. **A hydra.**

> Proven live: the same frame `c6a2dbaf9fbf21c5` served *identically* from `raw.githubusercontent.com`,
> `cdn.jsdelivr.net`, and `raw.githack.com` — three independent CDNs over one repo, today, zero setup.

## Principles

1. **The medium is data, not a service.** The whole state is files in a repo (append-only
   `events/` + materialized static `views/`). Reading requires no server and **no API you don't
   own on the critical path** — only static files over a CDN.
2. **Many heads, one body.** The same repo is served from N interchangeable heads. Each is a full copy.
3. **Trust the content, not the head.** Every artifact is content-addressed (`sha256`). The edge
   verifies the hash, so **any** head is safe to read from — even one you don't control.
4. **Read from any head; fail over.** Try heads in order until one answers. Losing the primary
   (takedown, geoblock, outage, account ban) costs nothing — the next serves identical, verified data.
5. **Re-seed from any copy.** The repo *is* the whole medium; anyone can clone/fork/mirror it to
   mint a new head. Cut every head and one surviving fork regrows the swarm.
6. **GitHub is a head, not the home.** We use it as the convenient primary, but the protocol is
   host-agnostic — point `FRAME_HEADS` at anything serving the repo's raw files over HTTPS.

## The head list

An edge carries an ordered list of head base-URLs (repo-relative paths are appended):

```
https://raw.githubusercontent.com/<owner>/<repo>/<ref>        GitHub raw            (live)
https://cdn.jsdelivr.net/gh/<owner>/<repo>@<ref>              jsDelivr CDN          (live, independent)
https://raw.githack.com/<owner>/<repo>/<ref>                  raw.githack CDN       (live)
https://<gitlab|codeberg host>/<owner>/<repo>/-/raw/<ref>     non-GitHub git mirror
https://<ipfs-gateway>/ipns/<key>                             IPFS (natively content-addressed)
… + any FRAME_HEADS you add (self-host, corporate mirror, torrent-backed gateway)
```

The minimum viable hydra is **one repo + the free CDN heads** — already live above. More heads = more survival.

## Read

`GET <head>/<path>` for each head in order until one returns; **verify the content hash**; the
first verified copy wins. Heads may be stale — verify against `net/latest.json`'s hash and prefer
the highest `tick` if heads disagree. **A stale head is a slow head, never a wrong one.**

## Write (append-only, host-agnostic)

The write path is a **git commit to any writable head**, never a proprietary API. A node with a
scoped deploy key commits an event to a head; head-to-head mirroring (`git push --mirror` /
multi-remote / a sync job / IPFS pin) propagates it. Reads need no auth; a write to any one head
eventually reaches all. An edge without write access buffers locally and flushes through its
public twin (see [rapp-frame SPEC §public twin](SPEC.md)).

## Mirroring (growing heads)

- **jsDelivr / raw.githack / statically.io** — zero-setup CDN heads over any GitHub repo (already live).
- A scheduled `git push --mirror` to **GitLab / Codeberg / a self-host**.
- **IPFS** — pin the repo, publish an IPNS name as a content-addressed head.
- Torrent / IPFS make the data **re-seedable by anyone**.

## Why it can't be shut down

Taking the swarm down requires taking down **every head simultaneously AND every fork AND every
cached copy** — and any survivor re-seeds the rest. The data is small, static, content-addressed,
and freely copyable. That is the cockroach property. **Cut a head, two grow.**

## Composition

- The transport under **[rapp-frame/1.0](SPEC.md)** — frames/echos are read over the hydra.
- The survival layer under the Foundation's *"canonical public twin for everything"* — every spec
  and static-API can be hydra-served.
- Routed by **[rapp-spine](https://github.com/kody-w/rapp-spine)** — situation: *"I must keep reading
  the swarm even if a host is taken down."*

---

*Cut one head, two grow. The medium is the data; the data is everywhere.*
