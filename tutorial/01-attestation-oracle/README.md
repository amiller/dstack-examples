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

The quote contains measured values. Compare them against reference values you trust:

| Measured (from quote) | Reference | Source |
|-----------------------|-----------|--------|
| Intel signature | Intel root CA | Built into dcap-qvl |
| MRTD, RTMR0-2 | Calculated from OS image | Download from [meta-dstack releases](https://github.com/Dstack-TEE/meta-dstack/releases) |
| compose-hash (RTMR3) | `sha256(app-compose.json)` | Build from your docker-compose.yaml |
| report_data | `sha256(statement)` | Hash the statement yourself |
| tlsFingerprint | Certificate fingerprint | Fetch from api.coingecko.com |

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
>   ...
> }
> ```
> The SHA-256 of this manifest is the **compose-hash** in RTMR3.
>
> **Important:** The `pre_launch_script` is included in the hash. Phala Cloud injects its own prelaunch script. To audit, fetch the complete `app-compose.json` via `phala cvms attestation <app>`. See [prelaunch-script](../../prelaunch-script) for the Phala Cloud script source.
>
> For standalone verification that builds app-compose.json locally: [attestation/configid-based](../../attestation/configid-based)

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

## Next Steps

- [02-persistence-and-kms](../02-persistence-and-kms): Derive persistent keys across restarts
- [03-gateway-and-ingress](../03-gateway-and-ingress): Custom domains and TLS

## SDK Reference

- **JS/TS**: `npm install @phala/dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/js)
- **Python**: `pip install dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/python)

## Files

```
01-attestation-oracle/
├── docker-compose.yaml  # Oracle app (self-contained)
├── verify_full.py       # Python verification script
└── README.md            # This file
```
