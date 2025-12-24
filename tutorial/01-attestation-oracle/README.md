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

To trust the oracle's output, verify:

1. **Quote is valid** — Hardware signature, OS integrity, compose hash
2. **report_data matches** — `sha256(statement) == reportDataHash` in quote
3. **TLS fingerprint is correct** — Matches the real CoinGecko certificate

### Step 1: Verify the Quote

The TDX quote proves the statement came from verified TEE code. Choose a verification method:

#### Option A: Hosted (no setup)

Visit [trust.phala.network](https://trust.phala.network) and enter your app's domain. It shows verification status for all Phala Cloud apps.

#### Option B: Local script (recommended)

Use the self-contained verification script from [attestation/configid-based](../../attestation/configid-based):

```bash
cd attestation/configid-based

# Download verification tools (dcap-qvl, dstack-mr, OS image)
./attest.sh download

# Calculate expected measurements from your compose file
./attest.sh compose
./attest.sh calc-mrs

# Verify a running app's quote
./attest.sh verify
```

This compares:
- **mr_config_id**: Contains your compose hash (SHA-256 padded to 96 chars)
- **MRTD/RTMR0-2**: Match expected values from [dstack OS release](https://github.com/Dstack-TEE/meta-dstack/releases)
- **Hardware signature**: Validated by Intel DCAP-QVL

#### Option C: Programmatic (trust-center API)

For integration into your own verification flow:

```bash
git clone https://github.com/Phala-Network/trust-center.git
cd trust-center && bun install
cd packages/verifier && bun run dev

# Then call the API
curl -X POST http://localhost:3000/verify \
  -H "Content-Type: application/json" \
  -d '{"appId": "<app-id>", "domain": "your-app.phala.network"}'
```

#### Option D: Python script (verify_full.py)

A standalone Python script included in this tutorial:

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

> **How verification proves code correspondence**
>
> Your `docker-compose.yaml` gets wrapped into an `app-compose.json` manifest:
> ```json
> {
>   "docker_compose_file": "<your compose content>",
>   "pre_launch_script": "#!/bin/bash\n...",
>   "kms_enabled": true,
>   "gateway_enabled": true,
>   ...
> }
> ```
> The SHA-256 of this manifest becomes the **compose-hash**, which is embedded in `mr_config_id` in the TDX quote.
>
> **Important:** The `pre_launch_script` is included in the hash. Phala Cloud injects its own prelaunch script (for SSH setup, environment config, etc.). To fully audit, you need the complete `app-compose.json` — fetch it via `phala cvms attestation <app>` or from trust-center's output. See [prelaunch-script](../../prelaunch-script) for the Phala Cloud script source.
>
> To verify a remote app matches your local code:
> 1. Build `app-compose.json` from your docker-compose (attest.sh `compose` does this)
> 2. Calculate `sha256(app-compose.json)` → your expected compose-hash
> 3. Get the remote app's quote and extract `mr_config_id`
> 4. Compare: if `mr_config_id` starts with your compose-hash, the app is running your code
>
> **trust-center vs attest.sh:**
> - **attest.sh**: You provide compose file + OS version. Fully local — downloads binaries (dcap-qvl, dstack-mr) and OS image from GitHub, calculates measurements, compares with quote. Works against any dstack instance.
> - **trust-center**: You provide appId/domain. Hybrid — fetches app metadata from Phala Cloud API (`cloud-api.phala.network`) and quote from the app's RPC endpoint, but runs verification (dcap-qvl, dstack-mr) locally. Downloads OS images from GitHub. Easier discovery but relies on Phala Cloud API for app lookup.
>
> See [attestation/configid-based](../../attestation/configid-based) for the standalone verification script.

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

## What This Proves

When all three checks pass:

1. **The code is correct** — Trust-center verified the docker-compose.yaml hash matches what's deployed
2. **The TEE is authentic** — Intel hardware signed the quote
3. **The statement is genuine** — report_data binds the exact statement to the quote
4. **The data source is real** — TLS fingerprint proves connection to the actual API server

This is the complete verification chain for a TEE oracle.

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
