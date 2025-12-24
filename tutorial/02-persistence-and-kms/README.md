# Tutorial 02: Persistence and KMS

How TEE apps derive persistent keys that survive restarts and migrations.

## The Problem

TEE memory is wiped on restart. If your app generates a private key at startup, it gets a new key every time — breaking wallets, signatures, and encryption.

## The Solution: `getKey()`

The dstack SDK's `getKey()` derives deterministic keys from a path:

```javascript
import { DstackClient } from '@phala/dstack-sdk'

const client = new DstackClient()
const { key } = await client.getKey('/my-app/wallet')
// Same path → same key, every time
```

The derived key is:
- **Deterministic**: Same path always returns the same key
- **Unique to your app**: Different apps get different keys for the same path
- **Persistent across restarts**: KMS stores the root key, your app derives from it

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                          KMS                                │
│  (runs in its own TEE, holds root keys per app_id)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ derives
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Your App                              │
│  getKey('/wallet')  →  deterministic key for this path     │
│  getKey('/signing') →  different key, same app             │
└─────────────────────────────────────────────────────────────┘
```

The KMS (Key Management Service) runs in a separate TEE and:
1. Holds a root key tied to your `app_id` (compose hash)
2. Derives child keys on request using the path you provide
3. Returns the same derived key for the same path

## Example: Persistent Wallet

```javascript
import { DstackClient } from '@phala/dstack-sdk'
import { privateKeyToAccount } from 'viem/accounts'

const client = new DstackClient()

// Derive a wallet key — same address every restart
const { key } = await client.getKey('/eth/main-wallet')
const privateKey = `0x${Buffer.from(key).toString('hex').slice(0, 64)}`
const account = privateKeyToAccount(privateKey)

console.log('Wallet address:', account.address)
// Always the same address for this app + path
```

## Key Paths

Use descriptive paths to organize your keys:

```javascript
// Different paths = different keys
await client.getKey('/wallet/eth/main')
await client.getKey('/wallet/eth/fee-payer')
await client.getKey('/signing/api-responses')
await client.getKey('/encryption/user-data')
```

## KMS Providers

Phala Cloud offers different KMS providers per cluster:

| Provider | Description |
|----------|-------------|
| `cloud` | Phala-operated KMS (default) |
| `onchain` | Keys anchored to on-chain governance |

The KMS provider is set at deployment time. Your app doesn't need to know which provider is used — `getKey()` works the same way.

## Verification

KMS itself runs in a TEE and is verified as part of the trust chain:
- trust-center verifies KMS attestation
- KMS public key is recorded in the app's attestation
- Key derivation is deterministic and auditable

See [trust-center](https://github.com/Phala-Network/trust-center) for KMS verification details.

## Try It

```bash
# Start simulator
phala simulator start

# Run a simple key derivation test
docker compose run --rm \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app
```

## Next Steps

- [01-attestation-oracle](../01-attestation-oracle): Binding data to attestation quotes
- [03-gateway-and-ingress](../03-gateway-and-ingress): Custom domains and TLS

## References

- [Key Management Protocol](https://docs.phala.network/dstack/design-documents/key-management-protocol)
- [Cloud vs On-chain KMS](https://docs.phala.network/phala-cloud/key-management/cloud-vs-onchain-kms)
