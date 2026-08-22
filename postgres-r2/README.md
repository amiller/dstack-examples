# Postgres that survives losing its disk

Your CVM was just redeployed. Where did your database go?

It's gone. A dstack app volume is cache-grade storage — the developer guide says so — and a
database sitting on one was never durable, only uninterrupted. This example stops treating the
disk as the database: Postgres ships every write-ahead log segment to an S3-compatible bucket
(Cloudflare R2 here) with [wal-g](https://github.com/wal-g/wal-g), and the disk becomes a cache
you can delete.

The part that makes it a TEE example rather than an ops recipe: **the encryption key is derived
from the app's identity, not handed to it.** The bucket holds bytes nobody can read — not
Cloudflare, not you — and the only thing that turns them back into a database is attested code
running under the same app id.

## Run it

```bash
phala deploy -n pg-r2 -c docker-compose.yml \
  -e AWS_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com \
  -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... \
  -e WALG_S3_PREFIX=s3://<bucket>/pg

./verify.sh pg-r2
```

No `POSTGRES_PASSWORD` and no encryption key in that command — both are derived at boot from
`GetKey` on the guest agent socket. The only secrets you pass are the bucket credentials, which
belong to Cloudflare's side of the arrangement and cannot be derived.

## The drill

The deployment is not the lesson. This is:

```bash
# 1. leave a canary
psql "$DSN" -c "CREATE TABLE canary(t timestamptz); INSERT INTO canary VALUES (now())"

# 2. wait for the segment to land (archive_timeout, 60s by default), then destroy the disk
phala ssh pg-r2 -- 'docker rm -f $(docker ps -q); docker volume rm <app>_pgdata'

# 3. bring the same app back, pointed at the archive
phala deploy --cvm-id pg-r2 -c docker-compose.yml -e RESTORE=true \
  -e AWS_ENDPOINT=... -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... \
  -e WALG_S3_PREFIX=s3://<bucket>/pg

# 4. the canary is still there
psql "$DSN" -c "SELECT * FROM canary"
```

Nothing was copied from the old node and no key was carried across. The app re-derived the key
because it is the same app.

> [!WARNING]
> **A different app cannot read this archive.** `GetKey` derives from app identity, so deploying
> this compose as a *new* CVM produces a different key and wal-g fails with `corrupted chunk` —
> that is decryption failing, not a damaged object. Measured on two CVMs running this exact
> example:
>
> ```
> pg-r2-example   /pg-r2/walg/v1 -> 736c54f314defc07…
> pg-r2-restored  /pg-r2/walg/v1 -> 160f640db26d2529…
> ```
>
> Restoring into a **new** app needs either the same app id (`phala deploy --custom-app-id <id>
> --nonce <n>`) or a supplied `WALG_LIBSODIUM_KEY` — and the moment you supply one, someone
> outside the enclave is holding the key you were trying not to have. Decide before your first
> backup, not after your last.

## What `verify.sh` proves

It is handed nothing. It re-derives the superuser password and logs in with it, then re-derives
the archive key — which it must, because without it wal-g cannot read the bucket at all.

```
== 1. keys are derived, not stored
   superuser path, twice   : b60a400df24a9af7… / b60a400df24a9af7…  same
   archive-key path        : 736c54f314defc07…  unrelated
   logging in with the re-derived password: postgres

== 2. the archive is current
   segments archived      : 6 (0 failed)
   newest segment is      : 72s old
   waiting to archive     : 0 .ready files

== 3. the bucket holds ciphertext
   a live segment on disk  : 16d10600010000000000000200000000
   the object in the bucket: d830dc91fa382fe4f6fea96b3008cfb1
   the object after wal-g  : 16d10600010000000000000600000000
   WAL magic is 16d1 — the bucket copy does not have it, the wal-g copy does
```

Every WAL page opens with the same magic for a given server version, so the magic is what
carries across segments; comparing whole heads would prove nothing.

## The numbers, with denominators

- **RPO — what a failure costs.** Whatever has not reached the archive yet. `archive_timeout` is
  the dial; at the default 60 s, a two-node version of this setup lost **54 of 73 acknowledged
  commits** when the primary was killed mid-write. Lower the timeout to narrow the window, at the
  cost of more and smaller objects.
- **RTO — how long the drill takes.** Restore time tracks the *compressed archive*, not the
  logical database: **333 MB of incompressible rows came back in 29.3 s** (about 11 MB/s), while
  1.18 GB of repetitive rows took 15.2 s because its archive is nearly empty, and an empty
  database hits a fixed-cost floor near 12 s. Measure your own data before promising anyone an RTO.

## How it works

- **Keys from `GetKey`.** `POST /GetKey` on `/var/run/dstack.sock` with a path returns 32 bytes of
  hex — exactly wal-g's libsodium key size — plus a signature chain. Same app and path, same key
  on every boot; different path, unrelated key. The derivation path carries the domain separation.
- **It fails closed.** No socket, or a derivation that returns something unusable, and the
  container exits. A database that would ship plaintext WAL into someone else's bucket should not
  start at all.
- **wal-g is pinned by sha256** and verified before it runs. Pulling an unverified binary into a
  measured enclave at boot gives away most of what the measurement was for.
- **TLS terminates inside the enclave**, so a client talks to Postgres rather than to the gateway.
  Connect with `sslnegotiation=direct` (libpq 17+) — the gateway routes `5432s` by peeking the TLS
  SNI, and libpq's default handshake gets dropped with a misleading "server closed the connection
  unexpectedly".
- **A base backup is pushed on first boot.** WAL alone restores nothing; it needs a base to replay
  onto, and a failure there is logged loudly.

## Not covered here

**High availability.** One node, no failover. Add streaming replication if you need the RPO window
closed rather than bounded.

**Archive rollback.** The bucket holds ciphertext, and a freshness check catches an archiver that
has stopped — but nothing here detects a storage provider that serves an *older* archive that is
internally consistent. wal-g will restore it and the result looks healthy at the wrong point in
history. Closing that needs a monotonic commitment to the archive head, kept somewhere the storage
provider does not control. It is the honest open problem in this design.

## Requirements

A CVM with egress to your object store and the guest agent socket mounted (both are in the
compose). Postgres 17, wal-g 3.0.9, any S3-compatible bucket.
