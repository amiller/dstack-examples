# Tutorial 05: On-Chain Authorization

Controlled multi-node deployment and custom authorization contracts.

## Prerequisites

Complete [03-keys-and-replication](../03-keys-and-replication) first. That tutorial covers:
- Signature chain verification
- Basic multi-node with `allowAnyDevice=true`

This tutorial covers **controlled** multi-node setups where the owner explicitly approves devices.

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

**Key insight:** The private key you deploy with becomes the **owner** of the AppAuth contract. The owner controls which devices and compose hashes are allowed.

## Deployment Options

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

### Option 2: Owner Adds Devices (Controlled Multi-Node)

Deploy first node, then the owner whitelists additional devices:

```bash
# Step 1: Deploy first node
phala deploy -n my-oracle -c docker-compose.yaml \
  --kms-id kms-base-prod5 \
  --private-key "$PRIVATE_KEY"

# Step 2: Add second device
cast send $APP_AUTH_ADDRESS "addDevice(bytes32)" $DEVICE_ID_2 \
  --private-key "$PRIVATE_KEY" --rpc-url https://mainnet.base.org

# Step 3: Deploy second node
python3 deploy_replica.py
```

### Option 3: allowAnyDevice

See [03-keys-and-replication](../03-keys-and-replication#multi-node-deployment) for the simpler `allowAnyDevice=true` approach.

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
DstackKms(KMS_ADDRESS).registerApp(yourContract);
```

**Examples:** NFT-gated, DAO-controlled, time-locked, multi-sig. See [09-extending-appauth](../09-extending-appauth).

## DstackApp Owner Functions

```solidity
function addDevice(bytes32 deviceId) external onlyOwner;
function removeDevice(bytes32 deviceId) external onlyOwner;
function addComposeHash(bytes32 composeHash) external onlyOwner;
function removeComposeHash(bytes32 composeHash) external onlyOwner;
function setAllowAnyDevice(bool allow) external onlyOwner;
function disableUpgrades() external onlyOwner;  // Permanent!
```

## On-Chain Verification Contract

`TeeOracle.sol` verifies the signature chain from [03-keys-and-replication](../03-keys-and-replication) on-chain:

```solidity
function verify(
    bytes32 messageHash,
    bytes calldata messageSignature,
    bytes calldata appSignature,
    bytes calldata kmsSignature,
    bytes calldata derivedCompressedPubkey,
    bytes calldata appCompressedPubkey,
    string calldata purpose
) public view returns (bool isValid)
```

## Test with Anvil

Test the full on-chain verification locally:

```bash
# Terminal 1: Start anvil
anvil &

# Terminal 2: Start oracle (with simulator)
phala simulator start
docker compose run --rm -p 8080:8080 \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock app

# Terminal 3: Run anvil test
pip install -r requirements.txt
python3 test_anvil.py
```

Output:
```
TeeOracle Anvil Test
============================================================
Oracle: http://localhost:8080
Anvil: http://localhost:8545
KMS Root: 0x8f2cF602C9695b23130367ed78d8F557554de7C5

Anvil connected, block: 0
Fetching from oracle...
  Price: $87436
  App ID: ea549f02e1a25fabd1cb788380e033ec5461b2ff
  App Pubkey: 02b85cceca0c02d878f0...
Deploying TeeOracle.sol...
  Contract: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Calling verify() on-chain...

============================================================
SUCCESS: On-chain verification passed
  - KMS signature verified
  - App signature verified
  - Message signature verified
```

## Files

```
05-onchain-authorization/
├── TeeOracle.sol              # On-chain signature verification
├── foundry.toml               # Foundry config (via-ir for stack depth)
├── test_anvil.py              # Test with local anvil
├── test_phalacloud.py         # Test on Phala Cloud
├── deploy_replica.py          # Deploy replica using existing appId
├── add_device.py              # Add device to whitelist (Option 2)
├── add_compose_hash.py        # Add compose hash to whitelist
├── docker-compose.yaml        # Oracle app (same as 03)
├── requirements.txt
└── README.md
```

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

## Next Steps

- [06-hardening-https](../06-hardening-https): Strengthen TLS verification
- [09-extending-appauth](../09-extending-appauth): Custom authorization contracts

## References

- [DstackKms.sol](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/DstackKms.sol)
- [DstackApp.sol](https://github.com/dstack-tee/dstack/blob/main/kms/auth-eth/contracts/DstackApp.sol)
- [NOTES.md](NOTES.md)
