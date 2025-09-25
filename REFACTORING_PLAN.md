# dstack-examples Refactoring Plan

## Current State Analysis

**Pending Examples Ready for Integration:**
- **Neko branch**: Complete webRTC-based headless browser example (PR #42)
- **Minecraft branch**: Working Minecraft server example with multiple connection methods

**Key Issues Found:**
- Open issues like "Timelock encryption example" (#3) labeled `good first issue` but no clear onboarding plan
- Current categorization mixes dev tools with compelling use cases
- Reproducible builds missing despite some examples (like dstack-ingress) implementing it well
- Agent-friendly patterns in heredoc branch not documented

## Comprehensive Refactoring Plan

### 1. Reproducible Builds Guide & Implementation

**Problem**: Examples lack attention to reproducible builds
**References**:
- [reproducible-builds-playground](https://github.com/Account-Link/reproducible-builds-playground) - Comprehensive deterministic build environment with verification
- [custom-domain/dstack-ingress/Dockerfile](./custom-domain/dstack-ingress/Dockerfile) - Production example with package pinning
**Solution**:
- Create `docs/REPRODUCIBLE_BUILDS.md` guide based on dstack-ingress patterns
- Audit all examples for reproducible build compliance
- Add build validation to dev.sh script
- Update CONTRIBUTING.md with reproducible build requirements

**Key patterns to document:**
- Using specific image digests (`@sha256:...`)
- Pinning package versions with snapshot.debian.org
- Deterministic build timestamps (`SOURCE_DATE_EPOCH=0`)
- Build script patterns like `./build-image.sh`

### 2. Integration of Pending Examples

**References**:
- [Neko PR #42](https://github.com/Dstack-TEE/dstack-examples/pull/42) - webRTC browser example
- [Minecraft branch](https://github.com/Dstack-TEE/dstack-examples/tree/amiller/minecraft) - Gaming server with multiple connection methods

**Neko Example** (PR #42):
- Merge and enhance documentation
- Position as "Remote GUI Access" use case
- Add security considerations for TEE GUI applications

**Minecraft Example**:
- Clean up and merge from minecraft branch
- Document multiple connection methods (ngrok, stunnel, socat)
- Position as "Gaming in TEE" showcase with security benefits

### 3. Issue-Based Onboarding Program

**References**:
- [Issue #3 - Timelock encryption example](https://github.com/Dstack-TEE/dstack-examples/issues/3) - Labeled "good first issue" but already implemented
- [GitHub Issues](https://github.com/Dstack-TEE/dstack-examples/issues) - Current issues lack structured onboarding approach

**Create structured contributor onboarding:**
- `docs/ONBOARDING.md` with clear progression path
- Label management: `good first issue`, `help wanted`, `mentorship available`
- Issue templates for different contribution types
- Monthly "contributor challenges" program

**Transform existing issues:**
- Issue #3 (Timelock encryption) → Already implemented, needs promotion
- Create new issues for missing examples
- Add difficulty ratings and mentorship offers

### 4. Reorganized Use Case Architecture

**References**:
- [Current README structure](./README.md) - Examples categorized as Security & Attestation, Networking & Domains, Development Tools, Advanced Use Cases
- Mix of compelling applications with developer utilities needs clearer separation

**Current problems:** Dev tools mixed with compelling use cases
**New structure:**

```
## 🎯 Compelling Use Cases
- **Privacy-Preserving Applications**
  - [timelock-nts](./timelock-nts) - Timelock decryption with NTS
  - [tor-hidden-service](./tor-hidden-service) - Anonymous services in TEE

- **Attenuated Authentication & User Consent**
  - [proof-of-user-optin](./proof-of-user-optin) - TEE-guaranteed one-time-use OAuth tokens
  - Based on [teleport.best](https://github.com/Account-Link/teleport-gramine-rs) - Long-lived but count-limited OAuth sessions
  - Addresses OAuth session management issues in dstack-examples GitHub issues

- **Proprietary Code Protection**
  - [dstack-semiproprietary-modules](https://github.com/Account-Link/dstack-semiproprietary-modules/) - Encrypted modules with AST analysis for safety verification
  - Smart contract-controlled code disclosure (crowdfund/vote-based release)

- **Provably Fair Gaming and E-Sports**
  - [minecraft](./minecraft) - Gaming servers with attestation

- **Social Media, Nooscopes, and Information Diet Apps**
  - [neko](./neko) - Remote browser with privacy guarantees
  - [xordi-automation](https://github.com/Account-Link/xordi-automation-devenv/) - Provable social media interaction logging
  - [verifiable-data-usage-bounds](./verifiable-data-usage-bounds) - Cryptographic evidence of staying within declared data usage limits

- **Provable AI Agents & LLM Applications**
  - [eliza-agent](https://docs.phala.com/phala-cloud/getting-started/explore-templates/launch-an-eliza-agent) - TEE-based conversational agents (documented but not in examples repo)
  - [llm-wrapper-app](./llm-wrapper-app) - Self-contained agent with value-add functionality over LLM queries
  - [sovereign-agents](./sovereign-agents) - TEE agents with proof of exclusive capability (inspired by [tee-hee-he](https://phala.com/posts/truth-of-AI-Agent))

- **Blockchain & DeFi**
  - [lightclient](./lightclient) - Trustless blockchain verification
  - [trustedsetup](./trustedsetup) - Cryptographic ceremony participation

## 🛠️ Developer Tools & Utilities
- **Getting Started & CLI**
  - [dstack-devops-playground](https://github.com/amiller/dstack-devops-playground) - CLI usage patterns, KMS practice, multi-server devops
  - [webshell](./webshell) - Container access for debugging
  - [launcher](./launcher) - Generic deployment patterns

- **Infrastructure Patterns**
  - [custom-domain](./custom-domain) - TLS certificate automation
  - [ssh-over-gateway](./ssh-over-gateway) - Secure tunneling
  - [distributed-database](https://github.com/amiller/dstack-examples/tree/database) - Distributed Postgres/Redis in TEE
  - [p2p-vpn](https://github.com/amiller/dstack-examples/tree/holepunch/p2p-wg) - Peer-to-peer VPN connections

- **Trust Minimization & Key Management**
  - [dstack-kms-basics](./dstack-kms-basics) - Key manager and simulator usage patterns
  - [trust-minimized-upgrades](./trust-minimized-upgrades) - Smart contract-based release process
  - [backdoor-removal-progression](./backdoor-removal-progression) - Gradual scaffolding removal as system stabilizes

## 🔒 Security & Attestation
- **Verification Examples**
  - [attestation/configid-based](./attestation/configid-based) - Production attestation
  - [attestation/rtmr3-based](./attestation/rtmr3-based) - Legacy verification
```

### 5. Single-File Application Pattern Documentation

**References**:
- [amiller/heredoc branch](https://github.com/Dstack-TEE/dstack-examples/tree/amiller/heredoc) - Contains agent-friendly patterns and style guidelines
- Shows improvements to dstack-ingress Dockerfile, README patterns, and configuration approaches

**Problem**: Tension between developer experience approaches:
- **Single docker-compose file**: Zero build step, immediate deployment, AI-agent friendly, but feels unconventional
- **Traditional Dockerfile + build**: Familiar to developers, unlimited flexibility, but requires build/push workflow

**Solution**: Embrace single-file style as a deliberate architectural choice for rapid prototyping
- Document when to use single-file vs multi-file approaches
- Provide patterns that make single-file applications production-viable
- Position as "rapid prototyping" → "production hardening" progression path
- Create agent-friendly documentation for working within single-file constraints

**Create `docs/SINGLE_FILE_PATTERNS.md`:**
- Heredoc patterns for multi-line environment variables and scripts
- Configuration templating within docker-compose
- When single-file reaches limits and needs traditional structure
- Migration path from single-file to multi-file examples

## Possible ordering

1. Plan how to integrate reproducible builds guide with dev.sh.
   - Gradual progression guide, from just works to reproducible
   - From reproducible to "trust minimized"
   - From "trust minimized" to "fully decentralized"
2. Restructure README with new categorization, and make progress on new / wip applications
   - neko / nooscope apps
   - provable user opt-in / consent
   - minecraft as fair gaming app
3. Create onboarding documentation
   - kms tutorials example
   - dstack devops example, ansible examples?
   - heredoc tutorial for agent-friendly examples
4. Transform issues into contributor challenges