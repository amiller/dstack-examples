# Tutorial 02: KMS and Signing

Derive persistent keys that survive restarts and produce on-chain verifiable signatures.

## The Problem

TEE memory is wiped on restart. If your app generates a private key at startup, it gets a new key every time — breaking wallets, signatures, and any persistent identity.

## The Solution: `getKey()`

The dstack SDK's `getKey()` derives deterministic keys from KMS:

```javascript
import { DstackClient } from '@phala/dstack-sdk'

const client = new DstackClient()
const result = await client.getKey('/oracle', 'ethereum')

// Derive an Ethereum wallet
const privateKey = '0x' + Buffer.from(result.key).toString('hex').slice(0, 64)
```

The derived key is:
- **Deterministic**: Same path → same key, every restart
- **Unique to your app**: Different apps (compose hashes) get different keys
- **Verifiable**: Signature chain proves the key came from KMS

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                          KMS                                │
│  (runs in its own TEE, holds root keys)                    │
│                                                             │
│  Root Key ──derives──▶ App Key ──derives──▶ Your Key       │
│     │                     │                    │            │
│     │                     │                    └─ getKey('/oracle')
│     │                     └─ tied to appId (compose hash)
│     └─ KMS root, known on-chain
└─────────────────────────────────────────────────────────────┘
```

The KMS returns a **signature chain** proving derivation:

```javascript
const result = await client.getKey('/oracle', 'ethereum')

result.key                    // Your derived key bytes
result.signature_chain[0]     // App signature: appKey signs derivedPubkey
result.signature_chain[1]     // KMS signature: kmsRoot signs appPubkey
```

## On-Chain Verification

The signature chain lets smart contracts verify a signature came from a TEE:

```
KMS Root (known on-chain: 0x2f83172A...)
    │
    │ signs: "dstack-kms-issued:" + appId + appPubkey
    ▼
App Key (recovered from kmsSignature)
    │
    │ signs: "ethereum:" + derivedPubkeyHex
    ▼
Derived Key → signs your messages
```

A contract can:
1. Recover `appPubkey` from `kmsSignature` and verify it matches KMS root
2. Recover `derivedPubkey` from `appSignature`
3. Verify the message signature against `derivedPubkey`

## Minimal Example

```javascript
import { DstackClient } from '@phala/dstack-sdk'
import { privateKeyToAccount } from 'viem/accounts'

const client = new DstackClient()

// Derive a persistent wallet
const result = await client.getKey('/wallet', 'ethereum')
const privateKey = '0x' + Buffer.from(result.key).toString('hex').slice(0, 64)
const account = privateKeyToAccount(privateKey)

console.log('Address:', account.address)  // Same every restart

// Sign a message
const signature = await account.signMessage({ message: 'hello' })
```

## Key Paths

Use paths to organize multiple keys:

```javascript
await client.getKey('/wallet/main')      // Main wallet
await client.getKey('/wallet/fees')      // Fee payer
await client.getKey('/signing/oracle')   // Oracle signatures
```

## Try It

```bash
phala simulator start

docker compose run --rm \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app
```

## Next Steps

- [01-attestation](../01-attestation): Understand TDX quotes and verification
- [04-onchain-oracle](../04-onchain-oracle): Full oracle with signature chain verification contract

## References

- [Key Management Protocol](https://docs.phala.network/dstack/design-documents/key-management-protocol)
- [DstackKms contract](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/DstackKms.sol)
