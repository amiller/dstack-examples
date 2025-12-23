# dstack Examples

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/Dstack-TEE/dstack?style=flat-square)](https://github.com/Dstack-TEE/dstack-examples/stargazers)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Community-blue?style=flat-square&logo=telegram)](https://t.me/+UO4bS4jflr45YmUx)
[![Documentation](https://img.shields.io/badge/Documentation-Phala%20Network-green?style=flat-square)](https://docs.phala.network/dstack)

**Example applications for [dstack](https://github.com/Dstack-TEE/dstack) - Deploy containerized apps to TEEs with end-to-end security in minutes**

[Use Cases](#use-cases) • [Core Patterns](#core-patterns) • [Dev Tools](#dev-scaffolding) • [Documentation](#documentation)

</div>

---

## Overview

This repository contains ready-to-deploy examples demonstrating how to build and run applications on [dstack](https://github.com/Dstack-TEE/dstack), the developer-friendly SDK for deploying containerized apps in Trusted Execution Environments (TEE).

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

Real-world applications you can build with dstack.

| Example | Description | Status |
|---------|-------------|--------|
| [8004-agent](./8004-agent) | Trustless AI agent with on-chain attestation and LLM access | Coming Soon |
| [oracle](./oracle) | TEE oracle returning JSON + signature + attestation bundle | Coming Soon |
| [mcp-server](./mcp-server) | Attested MCP tool server behind gateway | Coming Soon |
| [telegram-agent](./telegram-agent) | Telegram bot with TEE wallet and verified execution | Coming Soon |

---

## Core Patterns

Key building blocks for dstack applications.

### Attestation

How to get and verify TEE attestations.

| Example | Description | Status |
|---------|-------------|--------|
| [trust-center](./refs/trust-center) | Full attestation verification platform — **start here** for production attestation patterns | Reference |
| [attestation-sdk](./attestation-sdk) | Using Dstack client SDK to fetch attestations | Coming Soon |
| [timelock-nts](./timelock-nts) | Shows raw `/var/run/dstack.sock` usage (what the SDK wraps) | Available |
| [attestation/configid-based](./attestation/configid-based) | ConfigID-based verification (demonstrates current format) | Available |

### Gateway & Domains

TLS termination, custom domains, external connectivity.

| Example | Description |
|---------|-------------|
| [dstack-ingress](./custom-domain/dstack-ingress) | **Complete ingress solution** — auto SSL via Let's Encrypt, multi-domain, DNS validation, evidence generation with TDX quote chain |
| [custom-domain](./custom-domain/custom-domain) | Simpler custom domain setup via zt-https |

### Keys & Persistence

Persistent keys across deployments via KMS.

| Example | Description | Status |
|---------|-------------|--------|
| [get-key-basic](./get-key-basic) | `dstack.get_key()` — same key identity across machines | Coming Soon |

### On-Chain Interaction

Light client for reading chain state, anchoring outputs.

| Example | Description |
|---------|-------------|
| [lightclient](./lightclient) | Ethereum light client (Helios) running in enclave |

---

## Dev Scaffolding

Development and debugging tools. **Not for production.**

| Example | Description |
|---------|-------------|
| [webshell](./webshell) | Web-based shell access for debugging |
| [ssh-over-gateway](./ssh-over-gateway) | SSH tunneling through dstack gateway |
| [tcp-port-forwarding](./tcp-port-forwarding) | Arbitrary TCP port forwarding |

---

## Tech Demos

Interesting demonstrations.

| Example | Description |
|---------|-------------|
| [tor-hidden-service](./tor-hidden-service) | Run Tor hidden services in TEEs |

---

## Details

Implementation details and infrastructure patterns.

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
