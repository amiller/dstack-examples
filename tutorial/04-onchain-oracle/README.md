# Tutorial 04: On-Chain Verifiable Oracle

Build an oracle that signs price data with TEE-derived keys, verifiable on-chain. This tutorial demonstrates the **AppAuth contract** architecture that controls which TEEs can get keys from KMS.

## Understanding AppAuth

Every dstack app has an **AppAuth contract** on Base. When a TEE requests keys, KMS calls your AppAuth's `isAppAllowed()` to decide.

```
┌─────────────────────────────────────────────────────────────┐
│                    DstackKms Contract (Base)                 │
│                                                             │
│  registerApp(address) ← registers your AppAuth              │
│  isAppAllowed(bootInfo) → delegates to your contract        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ calls IAppAuth(appId).isAppAllowed(bootInfo)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Your AppAuth Contract (DstackApp)               │
│                                                             │
│  owner: 0x...  ← can add devices/hashes                     │
│  allowedDeviceIds[...]                                      │
│  allowedComposeHashes[...]                                  │
│  allowAnyDevice: true/false                                 │
│                                                             │
│  isAppAllowed(bootInfo) → checks whitelist                  │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** The private key you deploy with becomes the **owner** of the AppAuth contract. The owner can add devices and compose hashes to the whitelist.

## Four Deployment Options

### Option 1: Single Device (CLI Default)

```bash
phala deploy -n my-oracle -c docker-compose.yaml \
  --kms-id kms-base-prod5 \
  --private-key "$PRIVATE_KEY"
```

Creates AppAuth with:
- `owner` = address derived from PRIVATE_KEY
- `allowAnyDevice = false`
- `allowedDeviceIds[thisDevice] = true`
- `allowedComposeHashes[thisHash] = true`

**Result:** Only this device can get keys. Simple single-node deployment.

### Option 2: Owner Adds Devices (Recommended for Multi-Node)

Deploy first node, then the **owner** explicitly whitelists additional devices:

```bash
# Step 1: Deploy first node (owner = your address)
phala deploy -n my-oracle -c docker-compose.yaml \
  --kms-id kms-base-prod5 \
  --private-key "$PRIVATE_KEY"

# Step 2: Get device ID of second node (from Phala Cloud API)
# Step 3: Owner calls addDevice() on the AppAuth contract
cast send $APP_AUTH_ADDRESS "addDevice(bytes32)" $DEVICE_ID_2 \
  --private-key "$PRIVATE_KEY" --rpc-url https://mainnet.base.org

# Step 4: Deploy second node with same appId
python3 deploy_replica.py
```

**Result:** Controlled multi-node. Owner explicitly approves each device.

### Option 3: allowAnyDevice (Permissive)

Deploy with `allowAnyDevice=true` to let any TEE device get keys:

```bash
python3 deploy_with_contract.py  # Sets allowAnyDevice=true
```

The contract checks:
```solidity
function isAppAllowed(AppBootInfo calldata bootInfo) {
    if (!allowedComposeHashes[bootInfo.composeHash])
        return (false, "Compose hash not allowed");
    if (!allowAnyDevice && !allowedDeviceIds[bootInfo.deviceId])
        return (false, "Device not allowed");
    return (true, "");
}
```

**Result:** Any device with a whitelisted composeHash can join. Less secure but simpler.

### Option 4: Custom AppAuth Contract

Deploy your own contract implementing `IAppAuth`:

```solidity
interface IAppAuth {
    function isAppAllowed(AppBootInfo calldata bootInfo)
        external view returns (bool isAllowed, string memory reason);
}
```

Then register it:
```solidity
DstackKms(KMS_ADDRESS).registerApp(yourContract);  // Public function!
```

**Examples:**
- NFT-gated: Only NFT holders can run nodes
- DAO-controlled: Compose hashes approved by vote
- Time-locked: Deployments only during certain periods
- Multi-sig: Multiple approvals required

## DstackApp Owner Functions

The standard AppAuth (`DstackApp`) gives the owner these functions:

```solidity
// Whitelist management
function addDevice(bytes32 deviceId) external onlyOwner;
function removeDevice(bytes32 deviceId) external onlyOwner;
function addComposeHash(bytes32 composeHash) external onlyOwner;
function removeComposeHash(bytes32 composeHash) external onlyOwner;

// Mode toggle
function setAllowAnyDevice(bool allow) external onlyOwner;

// Upgrades
function disableUpgrades() external onlyOwner;  // Permanent!
```

## Signature Chain

Regardless of which option you use, the oracle proves its keys came from KMS:

```
KMS Root (known on-chain)
    │
    │ signs: "dstack-kms-issued:" + appId + appPubkey
    ▼
App Key (recovered from kmsSignature)
    │
    │ signs: "ethereum:" + derivedPubkeyHex
    ▼
Derived Key → signs oracle messages
```

## Quick Start (Local Simulator)

```bash
pip install -r requirements.txt
phala simulator start

docker compose build
docker compose run --rm -p 8080:8080 \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app

# In another terminal
python3 test_local.py
```

## Files

```
04-onchain-oracle/
├── docker-compose.yaml        # Oracle app
├── TeeOracle.sol              # On-chain signature verification
├── test_local.py              # Test with simulator
├── test_phalacloud.py         # Test on Phala Cloud
├── deploy_with_contract.py    # Deploy with allowAnyDevice=true (Option 3)
├── deploy_replica.py          # Deploy replica using existing appId
├── add_device.py              # Add device to whitelist (Option 2)
├── add_compose_hash.py        # Add compose hash to whitelist
├── requirements.txt
├── NOTES.md                   # Troubleshooting & CLI limitations
└── README.md
```

## Next Steps

- [05-hardening-https](../05-hardening-https): Strengthen TLS verification
- [07-lightclient](../07-lightclient): Read verified blockchain state

## Contract Addresses

| Contract | Address |
|----------|---------|
| DstackKms (Base) | `0x2f83172A49584C017F2B256F0FB2Dca14126Ba9C` |
| KMS Root (Simulator) | `0x8f2cF602C9695b23130367ed78d8F557554de7C5` |

## IAppAuth Interface

From [dstack/kms/auth-eth/contracts/IAppAuth.sol](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/IAppAuth.sol):

```solidity
struct AppBootInfo {
    address appId;
    bytes32 composeHash;
    address instanceId;
    bytes32 deviceId;
    bytes32 mrAggregated;
    bytes32 mrSystem;
    bytes32 osImageHash;
    string tcbStatus;
    string[] advisoryIds;
}

function isAppAllowed(AppBootInfo calldata bootInfo)
    external view returns (bool isAllowed, string memory reason);
```

## References

- [DstackKms.sol](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/DstackKms.sol)
- [DstackApp.sol](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/DstackApp.sol)
- [NOTES.md](NOTES.md)
