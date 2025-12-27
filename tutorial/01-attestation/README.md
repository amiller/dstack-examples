# Tutorial 01: Attestation

Build a TEE oracle and verify its attestation end-to-end.

This tutorial covers:
- Building an app that produces verifiable outputs
- Binding data to TDX quotes via `report_data`
- Multiple verification methods (hosted, scripts, programmatic)

## What it does

```
┌─────────────────────────────────────────────────────────────────┐
│                         TEE Oracle                              │
│                                                                 │
│  1. Fetch price from api.coingecko.com                         │
│  2. Capture TLS certificate fingerprint                        │
│  3. Build statement: { price, tlsFingerprint, timestamp }      │
│  4. Get TDX quote with sha256(statement) as report_data        │
│  5. Return { statement, quote }                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The TLS fingerprint proves which server the TEE connected to. The quote proves the statement came from this exact code running in a TEE.

## Run Locally

```bash
# Start the simulator
phala simulator start

# Run the oracle
docker compose run --rm \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app
```

## Endpoints

**GET /** — App info and available endpoints

**GET /price** — Attested BTC price
```json
{
  "statement": {
    "source": "api.coingecko.com",
    "price": 97234.00,
    "tlsFingerprint": "5A:3B:...:F2",
    "tlsIssuer": "Cloudflare, Inc.",
    "tlsValidTo": "Dec 31 2025",
    "timestamp": 1703347200000
  },
  "reportDataHash": "a1b2c3...",
  "quote": "BAACAQI..."
}
```

## Deploy to Phala Cloud

```bash
phala deploy -n tee-oracle -c docker-compose.yaml
```

---

## Verification

The quote contains **measured values**. Verification means comparing them against **reference values** you trust.

### Reference Values: Where They Come From

| Measured Value | Reference Value | Who Provides It |
|----------------|-----------------|-----------------|
| Intel signature | Intel root CA | Intel (built into dcap-qvl) |
| MRTD, RTMR0-2 | Hash of OS image | [meta-dstack releases](https://github.com/Dstack-TEE/meta-dstack/releases) |
| compose-hash (RTMR3) | `sha256(app-compose.json)` | **The developer** |
| report_data | `sha256(statement)` | Computed from output |
| tlsFingerprint | Certificate fingerprint | Fetch from api.coingecko.com |

This is the core insight: **attestation is only as trustworthy as your reference values.**

- Intel provides reference values for hardware authenticity
- Dstack maintainers provide reference values for the OS layer
- **The app developer must provide reference values for the application layer**

### Step 1: Validate Quote and Compare Measurements

Use the included Python script:

```bash
# Install verification tools
CFLAGS="-g0" cargo install dcap-qvl-cli
CGO_CFLAGS="-g0" go install github.com/kvinwang/dstack-mr@latest

# Get attestation from your deployed app
phala cvms attestation tee-oracle --json > attestation.json

# Download matching dstack OS image
curl -LO https://github.com/Dstack-TEE/meta-dstack/releases/download/v0.5.5/dstack-0.5.5.tar.gz
tar xzf dstack-0.5.5.tar.gz

# Verify
python3 verify_full.py attestation.json --image-folder dstack-0.5.5/
```

Output:
```
=== Step 1: Hardware Verification (dcap-qvl) ===
  ✓ Hardware verification passed

=== Step 2: Extract Measurements ===
  Compose hash (from quote): 392b8a1f...

=== Step 3: OS Verification (dstack-mr) ===
  ✓ MRTD matches - kernel/initramfs verified

=== Step 4: Compose Hash Verification ===
  ✓ MATCH - Compose hash verified!
```

---

> **About compose-hash**
>
> Your `docker-compose.yaml` gets wrapped into an `app-compose.json` manifest:
> ```json
> {
>   "docker_compose_file": "<your compose content>",
>   "pre_launch_script": "#!/bin/bash\n...",
>   "kms_enabled": true,
>   "salt": "random-hex-string",
>   ...
> }
> ```
> The SHA-256 of this manifest is the **compose-hash** in RTMR3.
>
> **Important:** The `pre_launch_script` is included in the hash. Phala Cloud injects its own prelaunch script. To audit, fetch the complete `app-compose.json` via `phala cvms attestation <app>`. See [prelaunch-script](../../prelaunch-script) for the Phala Cloud script source.
>
> For standalone verification that builds app-compose.json locally: [attestation/configid-based](../../attestation/configid-based)

### The app-compose.json Manifest

The compose-hash in RTMR3 is the SHA-256 of an `app-compose.json` manifest:

```json
{
  "manifest_version": 2,
  "name": "tee-oracle",
  "runner": "docker-compose",
  "docker_compose_file": "services:\n  app:\n    image: ...",
  "kms_enabled": true,
  "gateway_enabled": true,
  "public_logs": true,
  "public_sysinfo": true,
  "pre_launch_script": "#!/bin/bash\n...",
  "allowed_envs": [],
  "tproxy_enabled": true
}
```

**Where this comes from:**
- `docker_compose_file`: Your docker-compose.yaml content
- `pre_launch_script`: Default provided by Phala Cloud, can be customized
- Other fields: Deployment configuration options

**How to fetch it:**
- Deployed app: `phala cvms attestation <app> --json | jq .app_info.tcb_info.app_compose`
- Running on dstack: `curl localhost:8090/info`
- Simulator: Uses fixed manifest at `sdk/simulator/app-compose.json`

### Two Verification Approaches

Dstack supports two ways to verify compose-hash:

**ConfigID-based (v0.5.1+)** — simpler, used by this tutorial
- Compose-hash is stored directly in `mr_config_id` (padded to 96 chars)
- Just compare measurement registers to known good values
- See: [attestation/configid-based](../../attestation/configid-based)

**RTMR3-based** — older, more complex
- Compose-hash is an event in RTMR3's event log
- Must replay the event log: each event's digest is hashed in sequence
- Events include: `app-id`, `compose-hash`, `instance-id`, `key-provider`
- See: [attestation/rtmr3-based](../../attestation/rtmr3-based)

The `verify_full.py` in this tutorial uses ConfigID-based:
```python
config_id = report['mr_config_id']
verified_hash = config_id[2:66]  # Extract compose hash after '01' prefix
```

### Programmatic Verification

The `@phala/dstack-verifier` library handles both approaches automatically:

```typescript
import { VerificationService } from '@phala/dstack-verifier'

const service = new VerificationService()
const result = await service.verify({
  domain: 'myapp.phala.network',
}, {
  hardware: true,
  os: true,
  sourceCode: true,  // Verifies compose-hash
})

if (result.success) {
  console.log('Verification passed')
}
```

See [trust-center](https://github.com/phatcopy/trust-center) for the full verification platform and [Phala docs](https://docs.phala.com/phala-cloud/attestation/trust-center-verification) for detailed reference value explanations.

### Step 2: Verify report_data Binding

The quote's `report_data` field contains `sha256(statement)`. Verify it matches:

```bash
# Extract statement from response and hash it
cat response.json | jq -r '.statement | @json' | shasum -a 256

# Compare with reportDataHash in response
cat response.json | jq -r '.reportDataHash'
```

If they match, the statement is exactly what the TEE produced.

### Step 3: Verify TLS Fingerprint

The `tlsFingerprint` in the statement is the SHA-256 fingerprint of the API server's certificate. You can verify it matches CoinGecko's real certificate:

```bash
# Get CoinGecko's current certificate fingerprint
echo | openssl s_client -connect api.coingecko.com:443 2>/dev/null | \
  openssl x509 -fingerprint -sha256 -noout

# Compare with statement.tlsFingerprint
cat response.json | jq -r '.statement.tlsFingerprint'
```

---

## Critical Thinking: The Auditor's Perspective

> *This section appears throughout the tutorial. Each chapter examines a different trust assumption.*

### The Fundamental Question

As an auditor, your job is to answer: **"Does the deployed system behave according to the source code I reviewed?"**

TEE attestation helps, but only partially. The quote proves *some code* is running in isolated hardware. It gives you hashes. But hashes of what?

```
┌─────────────────────────────────────────────────────────────────┐
│                    The Reference Value Problem                  │
│                                                                 │
│   What you audit:     Source code, Dockerfile, docker-compose  │
│   What quote gives:   compose-hash = 0x392b8a1f...             │
│                                                                 │
│   The gap:  Can you compute 0x392b8a1f from what you audited?  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Trust Layers

Every TEE app has a trust stack. At each layer, ask: *"Where does the reference value come from?"*

| Layer | What You're Trusting | Reference Value Source |
|-------|---------------------|------------------------|
| Hardware | Intel TDX is secure | Intel's attestation infrastructure |
| Firmware | No backdoors in BIOS/firmware | Platform vendor |
| OS | Dstack boots what it claims | meta-dstack releases (open source, reproducible) |
| App | Code matches what was audited | **Developer-provided** |

The bottom three layers have established reference value sources. The app layer is the developer's responsibility.

### How Auditing Actually Works

An auditor doesn't just read code—they run it. The workflow:

1. **Read source** — Form a mental model of intended behavior
2. **Run locally** — Test that model: "does it actually do X? what happens if Y?"
3. **Conclude** — "This code behaves as I understand it. It's safe."

The auditor's conclusion is based on **what they ran**, not what they read. Reading code is necessary but not sufficient—you have to see it execute.

### The Behavioral Gap Threat

Here's the problem: what the auditor ran locally might differ from what's deployed.

```
┌─────────────────────────────────────────────────────────────────┐
│                    The Behavioral Gap                           │
│                                                                 │
│   Auditor builds locally  →  observes behavior A  →  "safe"    │
│   Production build        →  has behavior B (subtly different) │
│   Attestation proves      →  production runs *something*       │
│                                                                 │
│   The auditor certified behavior A.                            │
│   Production has behavior B.                                    │
│   The audit doesn't apply.                                      │
└─────────────────────────────────────────────────────────────────┘
```

This gap can arise from:
- Different dependency versions resolved at build time
- Timestamps or randomness affecting behavior
- Build environment differences (compiler, OS, architecture)
- Intentional divergence (malicious or accidental)

**The hash question isn't abstract.** When an auditor asks "does my local build produce the same hash as production?"—they're really asking: *"Is my local model of the system actually the production system, or just a similar-looking approximation?"*

### What Reproducibility Actually Provides

Reproducibility closes the behavioral gap. If:
- Auditor builds from source → gets hash X
- Production attestation shows → hash X

Then the auditor's local testing environment **is** the production system. Their conclusions apply. The audit is meaningful.

Without reproducibility, the auditor has two options:
1. **Trust the developer's build** — "I audited something similar, probably fine"
2. **Pull the production image and diff manually** — Tedious, error-prone, incomplete

Neither is satisfactory. Reproducibility makes the audit rigorous.

### The Smart Contract Analogy

Smart contracts solved this problem:
- Source code on Etherscan
- Compiler version specified
- Anyone can recompile and verify the bytecode matches on-chain codehash
- DYOR is actually possible

TEE apps need the same pattern. The attestation is like the on-chain codehash. But without reproducible builds, there's no way to connect it back to auditable source.

---

**Next:** [01a-reproducible-builds](../01a-reproducible-builds) shows how developers can provide the evidence auditors need—and protect against bitrot that breaks verification over time.

---

## Next Steps

- [01a-reproducible-builds](../01a-reproducible-builds): Make builds verifiable for auditors
- [02-kms-and-signing](../02-kms-and-signing): Derive persistent keys and sign messages
- [03-gateway-and-tls](../03-gateway-and-tls): Custom domains and TLS

## SDK Reference

- **JS/TS**: `npm install @phala/dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/js)
- **Python**: `pip install dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/python)

## Files

```
01-attestation/
├── docker-compose.yaml  # Oracle app (quick-start, non-reproducible)
├── verify_full.py       # Attestation verification script
└── README.md
```
