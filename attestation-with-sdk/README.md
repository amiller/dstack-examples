# Attestation SDK Example

Minimal example showing how to use the [Dstack client SDK](https://github.com/Dstack-TEE/dstack/tree/master/sdk) to fetch TEE attestations.

## What it does

```javascript
import { DstackClient } from '@phala/dstack-sdk'

const client = new DstackClient()
const info = await client.info()           // App info (app_id, tcb_info, etc)
const quote = await client.getQuote(data)  // TDX quote with custom report_data
const key = await client.getKey(path)      // Derive deterministic key from path
```

The SDK wraps the raw `/var/run/dstack.sock` API. Results are served at `http://localhost:8080`.

## Local Development

Test locally using the dstack simulator:

```bash
# Start the simulator
phala simulator start

# Run the example (mounts simulator socket)
docker compose run --rm \
  -v ~/.phala-cloud/simulator/0.5.3/dstack.sock:/var/run/dstack.sock \
  app
```

## Deploy to Phala Cloud

```bash
phala deploy -n attestation-with-sdk -c docker-compose.yaml
```

**Note**: Requires dstack OS 0.5.x+ (uses `/var/run/dstack.sock`). Older 0.3.x images use `/var/run/tappd.sock` which is not compatible with the current SDK.

## Verify with Trust Center

Once deployed, verify your attestation using [trust-center](https://github.com/Phala-Network/trust-center):

1. Get your app's attestation endpoint (e.g., `https://your-app.phala.network/`)
2. Submit to trust-center for verification
3. Trust-center validates: hardware quote → OS integrity → compose hash → domain (if applicable)

## SDK Reference

- **JS/TS**: `npm install @phala/dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/js)
- **Python**: `pip install dstack-sdk` — [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/python)
- **Go**: [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/go)
- **Rust**: [docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/rust)
- **Raw curl**: [API docs](https://github.com/Dstack-TEE/dstack/tree/master/sdk/curl)
