# P2P WireGuard Network Demo

A demonstration of peer-to-peer WireGuard networking techniques, developed as a reference implementation for [dstack](https://github.com/Dstack-TEE/dstack), an experimental SDK for deploying Docker-based applications in Trusted Execution Environments (TEEs).

## Related Documentation
- [dstack](https://github.com/Dstack-TEE/dstack) - SDK for deploying applications in Intel TDX environments
- Part of the peer-to-peer CVM (Confidential Virtual Machine) clustering functionality

## Concept Demonstration
This demo shows:
- Dynamic peer discovery using a simple Gist as coordination point
- Position-based IP assignment (10.88.0.x based on list position)
- Automatic NAT traversal for full cone NATs
- Built-in connectivity testing

## How It Works
- Uses a Gist for peer list coordination
- Each node gets an IP based on its position in the list
- Automatic WireGuard setup and peer discovery
- Enhanced STUN handling for NAT traversal
- Built-in connectivity monitoring and testing

## Running the Demo
1. Create a Gist with your peer URLs
2. Update GIST_URL in docker-compose.yml
3. Run `docker compose up -d` on each machine

## Important Limitations
- Demonstration purposes only - not for production use
- Works with full cone NATs only
- Requires different public IPs (hairpin NAT won't work)
- If TCP port 8080 isn't accessible, use ngrok free tier as a workaround:
  ```bash
  ngrok http 8080
  ```
  Then put the ngrok URL in your Gist
