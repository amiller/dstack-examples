# Dstack Tutorial: Building DevProof Applications

This tutorial teaches you to build **DevProof** (or "unruggable") applications using Dstack — apps where even the developer can't cheat users.

## Why DevProof?

If you follow typical Dstack guides, you'll get an ordinary server where you (the admin) can still "rug" your users. The app runs in a TEE, but the developer retains backdoors.

**DevProof** is a different threat model: we assume the developer themselves might be malicious, and design the system so they *can't* betray users even if they wanted to.

This is what smart contracts and DeFi aspire to, but TEEs let us apply it to practical, general-purpose code — not just on-chain logic.

### Examples of DevProof reasoning

| Application | DevProof property |
|-------------|-------------------|
| Oracle for prediction markets | Developer can't manipulate how bets settle |
| Verifiable credentials (zkTLS) | Developer can't forge credentials |
| User consent collection | Developer can prove they collected N consents |
| Data handling | Developer can prove no user data was exposed |

### Analogies from Smart Contracts

Smart contracts achieve DevProof design through:
- Open source code
- On-chain codehash compared against verifiable builds
- Users expected to DYOR (do your own research)
- Auditors verify source and on-chain deployment match
- Immutable by default; upgrade mechanisms become audit surfaces
- Upgrade policies with on-chain "due process" (timelocks, multisig)

TEE apps need similar patterns — this tutorial shows how.

## Running Example: TEE Oracle

Throughout this tutorial, we build a **price oracle** for prediction markets:
1. Fetches prices from external APIs
2. Proves the data came from a specific TLS server
3. Signs results with TEE-derived keys
4. Verifiable on-chain

Each section adds a layer until we have a fully DevProof oracle.

---

## Development Environment

### Option 1: Plain Docker Compose

```bash
docker compose up
```

Most examples run without any TEE-specific setup. The dstack SDK calls (`getKey()`, `tdxQuote()`) will fail, but you can still test the rest of your application logic.

### Option 2: Phala Simulator

```bash
# Install Phala CLI
npm install -g @phala/cloud-cli

# Start the simulator
phala simulator start

# Run with simulated dstack socket
docker compose run --rm \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app
```

The simulator provides a mock dstack socket so `getKey()` and attestation calls work locally.

### Option 3: Phala Cloud

```bash
phala deploy -n my-app -c docker-compose.yaml
```

### Option 4: Self-hosted Dstack

See [Dstack TEE documentation](https://docs.phala.com/dstack/local-development) for running your own TDX nodes.

> **Note:** A DevProof design minimizes dependency on any single provider. These are just deployment options — the verification techniques in this tutorial work regardless of where you run.

### SDK Options

| Language | Install | Docs |
|----------|---------|------|
| JavaScript/TypeScript | `npm install @phala/dstack-sdk` | [sdk/js](https://github.com/Dstack-TEE/dstack/tree/master/sdk/js) |
| Python | `pip install dstack-sdk` | [sdk/python](https://github.com/Dstack-TEE/dstack/tree/master/sdk/python) |

---

## Tutorial Sections

### Core Tutorial

1. **[01-attestation](./01-attestation)** — Build a TEE oracle and verify its attestation end-to-end
2. **[02-kms-and-signing](./02-kms-and-signing)** — Derive persistent keys and verify signature chains
3. **[03-gateway-and-tls](./03-gateway-and-tls)** — Custom domains and TLS certificate verification
4. **[04-onchain-oracle](./04-onchain-oracle)** — AppAuth contracts and multi-node deployment
5. **[05-hardening-https](./05-hardening-https)** — OCSP stapling, CRL checking, CT records

### Advanced

6. **[06-encryption-freshness](./06-encryption-freshness)** — Encrypted storage, integrity, rollback protection
7. **[07-lightclient](./07-lightclient)** — Verified blockchain state via Helios light client
8. **[08-extending-appauth](./08-extending-appauth)** — Custom authorization contracts (timelocks, NFT-gating, multisig)

---

## References

- [Dstack Documentation](https://docs.phala.com/dstack)
- [Phala Cloud](https://cloud.phala.network)
- [trust-center](https://github.com/Phala-Network/trust-center) — Attestation verification
- [dstack GitHub](https://github.com/Dstack-TEE/dstack)
