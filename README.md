# dstack Examples

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/Dstack-TEE/dstack?style=flat-square)](https://github.com/Dstack-TEE/dstack-examples/stargazers)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Community-blue?style=flat-square&logo=telegram)](https://t.me/+UO4bS4jflr45YmUx)
[![Documentation](https://img.shields.io/badge/Documentation-Phala%20Network-green?style=flat-square)](https://docs.phala.network/dstack)

**Example applications for [dstack](https://github.com/Dstack-TEE/dstack) - Deploy containerized apps to TEEs with end-to-end security in minutes**

[Use Cases](#use-cases) • [Architecture Walkthrough](#architecture-walkthrough) • [Dev Tools](#dev-scaffolding) • [Documentation](#documentation)

</div>

---

## Overview

This repository contains ready-to-deploy examples demonstrating how to build and run applications on [dstack](https://github.com/Dstack-TEE/dstack), the developer-friendly SDK for deploying containerized apps in Trusted Execution Environments (TEE).

The examples are organized to follow the **TEE+EVM design patterns** from [ERC-733](https://erc733.org), walking through the key architectural layers: attestation, gateway/interoperability, key management, and on-chain interaction.

## Prerequisites

- Access to a dstack environment (self-hosted or [Phala Cloud](https://cloud.phala.network))
- Basic understanding of [TEE concepts](https://docs.phala.network/dstack)
- Basic familiarity with Docker Compose
- Git for cloning the repository

```bash
git clone https://github.com/Dstack-TEE/dstack-examples.git
cd dstack-examples
```

---

## Use Cases

Real-world applications that serve as **reference implementations** for ERC-733 TEE+EVM patterns.

| Example | Description | Status |
|---------|-------------|--------|
| [8004-agent](./8004-agent) | Trustless AI agent (ERC-8004) with on-chain attestation, LLM access via TLS | Coming Soon |
| [oracle](./oracle) | TEE oracle returning JSON + signature + attestation bundle | Coming Soon |
| [mcp-server](./mcp-server) | Attested MCP tool server behind gateway | Coming Soon |
| [telegram-agent](./telegram-agent) | Telegram bot with TEE wallet and verified execution | Coming Soon |

---

## Architecture Walkthrough

These examples teach the **layered TEE+EVM architecture** from ERC-733. Work through them in order to understand how dstack applications are built.

### 1. Attestation Layer

The foundation: establish trust by verifying and committing the enclave's code measurement on-chain.

| Example | Description |
|---------|-------------|
| [attestation/configid-based](./attestation/configid-based) | ConfigID-based remote attestation verification |
| [timelock-nts](./timelock-nts) | Timelock decryption using NTS (Network Time Security) |

**What you learn:** Code measurement, attestation documents, X.509 verification, secp256k1 enclave keys.

### 2. Gateway Layer

Interoperability: TLS termination inside the enclave, domain routing, external connectivity.

| Example | Description |
|---------|-------------|
| [custom-domain](./custom-domain) | Custom domain with automatic TLS via zt-https (model of dstack gateway) |

**What you learn:** TLS termination in enclave, DNS → TLS → route pattern, reverse proxy.

### 3. Keys & Replication Layer

Production reality: persistent keys across machines, crash recovery, upgrades.

| Example | Description | Status |
|---------|-------------|--------|
| [get-key-basic](./get-key-basic) | `dstack.get_key()` — same key identity across deployments | Coming Soon |

**What you learn:** KMS interaction, secrets replication, upgrade policies, dev-proofness.

### 4. On-Chain Interaction Layer

Blockchain integration: light client for reading chain state, coprocessor pattern for anchoring outputs.

| Example | Description |
|---------|-------------|
| [lightclient](./lightclient) | Ethereum light client (Helios) running in enclave |

**What you learn:** Light client in TEE, verifying on-chain state, coprocessor receipts.

---

## Dev Scaffolding

Development and debugging tools. **Not for production** — useful during development.

| Example | Description |
|---------|-------------|
| [webshell](./webshell) | Web-based shell access for debugging |
| [ssh-over-gateway](./ssh-over-gateway) | SSH tunneling through dstack gateway |
| [tcp-port-forwarding](./tcp-port-forwarding) | Arbitrary TCP port forwarding |

---

## Tech Demos

Interesting demonstrations — cool tech but not yet fully developed use cases with clear security stories.

| Example | Description |
|---------|-------------|
| [tor-hidden-service](./tor-hidden-service) | Run Tor hidden services in TEEs |

---

## Details

Implementation details and infrastructure patterns. Not primary use cases.

| Example | Description |
|---------|-------------|
| [launcher](./launcher) | Generic launcher pattern for Docker Compose apps |
| [prelaunch-script](./prelaunch-script) | Pre-launch script patterns (Phala Cloud) |
| [private-docker-image-deployment](./private-docker-image-deployment) | Using private Docker registries |
| [attestation/rtmr3-based](./attestation/rtmr3-based) | RTMR3-based attestation (legacy) |

---

## Documentation

- **[dstack Documentation](https://docs.phala.network/dstack)** - Official platform documentation
- **[Main Repository](https://github.com/Dstack-TEE/dstack)** - Core dstack framework
- **[ERC-733](https://erc733.org)** - TEE+EVM design patterns standard
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute

## Development

```bash
./dev.sh help              # Show available commands
./dev.sh validate <example> # Validate a specific example
./dev.sh validate-all      # Validate all examples
```

## Community

- **Telegram**: [Join our community](https://t.me/+UO4bS4jflr45YmUx)
- **Issues**: [GitHub Issues](https://github.com/Dstack-TEE/dstack-examples/issues)

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<div align="center">

**[⬆ Back to top](#dstack-examples)**

</div>
