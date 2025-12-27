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

**You can complete the entire tutorial without TDX hardware.** The simulator provides everything needed to develop and test locally.

### Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| Docker | Run apps | [docker.com](https://docker.com) |
| Phala CLI | Simulator + deploy | `npm install -g @phala/cloud-cli` |
| Python 3 | Test scripts | System package |
| Foundry | On-chain testing (04) | [getfoundry.sh](https://getfoundry.sh) |

### Local Development (Simulator)

```bash
# Start the simulator (provides mock KMS + attestation)
phala simulator start

# Run any tutorial section
cd 02-kms-and-signing
docker compose build
docker compose run --rm -p 8080:8080 \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app

# Run tests
pip install -r requirements.txt
python3 test_local.py
```

The simulator provides:
- `getKey()` — deterministic key derivation
- `tdxQuote()` — mock attestation quotes
- Signature chains verifiable against simulator KMS root

### On-Chain Testing (Anvil)

For [04-onchain-oracle](./04-onchain-oracle), use anvil for local contract testing:

```bash
anvil &                    # Local Ethereum node
forge create TeeOracle.sol # Deploy verification contract
```

### Production Deployment

```bash
# Phala Cloud (managed TDX)
phala deploy -n my-app -c docker-compose.yaml

# Self-hosted TDX
# See https://docs.phala.com/dstack/local-development
```

> **Note:** A DevProof design minimizes dependency on any single provider. The verification techniques work regardless of where you deploy.

### SDK Options

| Language | Install | Docs |
|----------|---------|------|
| JavaScript/TypeScript | `npm install @phala/dstack-sdk` | [sdk/js](https://github.com/Dstack-TEE/dstack/tree/master/sdk/js) |
| Python | `pip install dstack-sdk` | [sdk/python](https://github.com/Dstack-TEE/dstack/tree/master/sdk/python) |

---

## Tutorial Sections

### Core Tutorial

1. **[01-attestation](./01-attestation)** — Build a TEE oracle and verify its attestation end-to-end
   - **[01a-reproducible-builds](./01a-reproducible-builds)** — Make builds verifiable for auditors
2. **[02-kms-and-signing](./02-kms-and-signing)** — Derive persistent keys and verify signature chains
3. **[03-gateway-and-tls](./03-gateway-and-tls)** — Self-signed TLS with attestation-bound certificates
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
