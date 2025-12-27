# Tutorial 03: TLS and Connectivity

Self-signed TLS with attestation-bound certificates.

## Prerequisites

Complete [01-attestation](../01-attestation) first. This tutorial builds on attestation verification.

## The Problem

TEE apps need TLS, but:
- The dstack gateway terminates TLS → gateway sees plaintext
- Let's Encrypt requires DNS control → adds complexity
- Trusting a relay service (ngrok) to terminate TLS → breaks TEE integrity

## The Solution: Attestation-Bound Certificates

The TEE generates a self-signed certificate. The certificate fingerprint is included in the attestation. Clients verify:

```
1. Connect to TEE (ignore cert validation initially)
2. Fetch attestation from /attestation endpoint
3. Validate attestation (quote, measurements, etc.)
4. Extract cert fingerprint from attestation
5. Verify the TLS cert matches the attested fingerprint
6. Now the connection is trusted end-to-end
```

This works regardless of how you reach the TEE - gateway, ngrok, direct IP, etc.

## Architecture

```
┌────────┐         ┌─────────┐         ┌─────────────────────────┐
│ Client │ ─ TLS ─ │ Relay   │ ─ TLS ─ │ TEE                     │
│        │         │ (ngrok) │         │ ┌─────────────────────┐ │
│        │         │         │         │ │ Self-signed cert    │ │
│        │         │         │         │ │ Attestation includes│ │
│        │         │         │         │ │ cert fingerprint    │ │
│        │         │         │         │ └─────────────────────┘ │
└────────┘         └─────────┘         └─────────────────────────┘
           relay only sees
           encrypted TLS traffic
```

## Oracle with Self-Signed TLS

Building on the oracle from [02-kms-and-signing](../02-kms-and-signing), we add:
- Self-signed TLS certificate generated at startup
- Certificate fingerprint included in `/attestation` response

```yaml
services:
  app:
    build:
      context: .
      dockerfile_inline: |
        FROM node:22-slim
        RUN apt-get update && apt-get install -y openssl
        WORKDIR /app
        RUN npm init -y && npm install @phala/dstack-sdk viem
        COPY index.mjs .
        CMD ["node", "index.mjs"]
    ports:
      - "8443:8443"
    volumes:
      - /var/run/dstack.sock:/var/run/dstack.sock
```

## index.mjs

See [index.mjs](index.mjs) for the full implementation. Key points:

```javascript
// Generate self-signed cert at startup
execSync(`openssl req -x509 -newkey rsa:2048 ... -subj "/CN=tee-oracle"`)

// Hash the DER-encoded certificate (matches what TLS clients see)
const certDer = Buffer.from(pemToDer(certPem), 'base64')
const certFingerprint = createHash("sha256").update(certDer).digest("hex")

// Include fingerprint in attestation
app.get("/attestation", async (req, res) => {
  const reportData = Buffer.from(certFingerprint, "hex")
  const quote = await client.getQuote(reportData)
  res.json({ certFingerprint, quote: quote.quote.toString("hex"), ... })
})
```

## Verification Script

See [verify_tls.py](verify_tls.py) for the full implementation. The script:

1. Connects to the endpoint and extracts the TLS certificate fingerprint
2. Fetches `/attestation` (ignoring cert validation initially)
3. Verifies the certificate fingerprint matches what's in the attestation
4. Verifies the attestation quote itself

```
$ python3 verify_tls.py https://localhost:8443

Verifying: https://localhost:8443

1. Connecting and getting certificate...
   Certificate fingerprint: 789b0a77f2ad4b17...
2. Fetching attestation...
   Attested fingerprint:    789b0a77f2ad4b17...
3. Verifying certificate matches attestation...
   Certificate fingerprint matches attestation
4. Verifying attestation...
   Quote present (full verification requires trust-center)

============================================================
SUCCESS: TLS certificate is bound to TEE attestation
The connection is end-to-end secure regardless of relay.
```

## Testing Locally

```bash
# Terminal 1: Start simulator
phala simulator start

# Terminal 2: Run oracle with TLS
docker compose build
docker compose run --rm -p 8443:8443 \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock app

# Terminal 3: Verify
python3 verify_tls.py https://localhost:8443
```

## Connectivity Options

The verification works regardless of how you reach the TEE - the attestation binds the certificate.

| Method | TLS Termination | Trust Path |
|--------|-----------------|------------|
| Direct (localhost) | Your App TEE | Single TEE |
| Self-signed + attestation | Your App TEE | Single TEE |
| dstack gateway | Gateway TEE | Gateway TEE → Your App TEE |
| dstack-ingress | Your App TEE | Single TEE (with Let's Encrypt) |
| ngrok TCP tunnel | Your App TEE | Single TEE (ngrok is transport only) |

### For Production

**dstack-ingress** handles Let's Encrypt inside the TEE using DNS-01 challenges (no inbound port 80 needed). See [dstack-ingress](../../custom-domain/dstack-ingress) for setup.

### About the dstack Gateway

The dstack gateway is itself a TEE application - it's a dstack docker compose running in its own enclave. TLS termination happens inside the gateway's TEE, not in untrusted infrastructure.

**Audit surface:** When using the gateway, verifying the gateway's attestation becomes part of your trust assumptions. The gateway code is open source and scheduled for security audit.

For maximum isolation (single TEE in the trust path), use the self-signed + attestation approach from this tutorial or dstack-ingress.

## Files

```
03-gateway-and-tls/
├── docker-compose.yaml    # Oracle with self-signed TLS
├── index.mjs              # HTTPS server with attestation
├── verify_tls.py          # Verification script
└── README.md
```

## Next Steps

- [04-onchain-oracle](../04-onchain-oracle): AppAuth contracts and on-chain verification
- [05-hardening-https](../05-hardening-https): Let's Encrypt with dstack-ingress

## Key Insight

**The certificate doesn't need to be signed by a CA.** The attestation IS the trust anchor. By binding the certificate fingerprint to a valid TEE attestation, we prove the certificate was generated inside the TEE. This pattern works for any self-signed credential.
