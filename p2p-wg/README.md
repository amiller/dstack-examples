# P2P WireGuard Network for dstack

This project demonstrates how to establish peer-to-peer WireGuard VPN connections between nodes in a [dstack](https://github.com/Dstack-TEE/dstack) network, solving a key challenge in Trusted Execution Environment (TEE) networking.

## The Challenge: UDP in dstack

While [dstack](https://github.com/Dstack-TEE/dstack) excels at providing secure TLS and HTTP routing for containerized applications in TEEs, it doesn't directly facilitate UDP traffic routing. This presents a challenge for WireGuard VPN connections, which rely on UDP for their encrypted tunnels. The dstack gateway can route HTTP traffic to your containers using patterns like `<id>-<port>.app.kvin.wang`, but WireGuard needs direct UDP connectivity between peers.

## The Solution: Distributed Coordination

Our approach creates something akin to a distributed Tailscale, but without relying on a single coordination server. Instead, we leverage dstack's existing TLS routing capabilities for connection metadata while allowing WireGuard to establish direct UDP tunnels between nodes.

The architecture works in three key phases:

**Phase 1: Metadata Exchange via HTTPS**  
Each dstack node exposes its connection information through dstack's TLS routing. When a container starts, it publishes a `/node.json` endpoint containing its WireGuard public key and NAT-discovered external IP address and port. This metadata is accessible via dstack's secure HTTPS routing, ensuring that connection information can be exchanged even through restrictive firewalls.

**Phase 2: Peer Discovery via Gist**  
Rather than using a centralized coordination server, we maintain a simple JSON list of peer URLs in a GitHub Gist. Each node polls this list to discover other peers in the network. While we currently use a Gist for simplicity, the design anticipates migrating to smart contract-based coordination, aligning with dstack's vision of on-chain key management for truly decentralized infrastructure.

**Phase 3: Direct UDP Connection via Hole Punching**  
Once peers have exchanged metadata through the HTTPS channels, WireGuard attempts direct UDP connections. Each node uses STUN discovery to determine its external IP and port, then configures WireGuard peers with these endpoints. WireGuard's protocol naturally performs UDP hole punching, allowing peers behind NAT to establish direct encrypted tunnels without requiring a relay server.

## Key Components

The system consists of a single Python application that coordinates several essential functions:

The **STUN client** periodically probes external STUN servers to discover the node's public IP address and port mapping. This happens only when no active peer connections exist, minimizing unnecessary network traffic while ensuring connectivity information stays current.

The **HTTP server** exposes the `/node.json` endpoint through dstack's TLS routing, allowing other peers to discover this node's WireGuard public key and connection details. This server also provides a `/test` endpoint on the WireGuard overlay network for connectivity verification.

The **peer discovery loop** polls the Gist for the current list of peer URLs, fetches each peer's `/node.json`, and dynamically reconfigures WireGuard connections as the network topology changes. The system handles peer additions, removals, and IP address changes gracefully.

The **WireGuard manager** automatically generates keypairs, configures network interfaces, and manages peer connections. It assigns overlay IP addresses based on each node's position in the peer list (10.88.0.10+index), ensuring consistent addressing across the network.

## Network Topology

The overlay network uses a simple position-based addressing scheme. Each node's IP address in the 10.88.0.0/24 subnet corresponds to its index in the peer list, with a base offset of 10 (so the first node gets 10.88.0.10, second gets 10.88.0.11, etc.). This deterministic approach means that reordering the peer list will trigger IP reassignments across the network, so the list should be kept stable once established.

Nodes continuously test connectivity by making HTTP requests to each other's `/test` endpoints over the WireGuard overlay. This provides immediate feedback about tunnel health and helps diagnose connectivity issues.

## Getting Started

Create a GitHub Gist containing a JSON array listing your node URLs:

```json
[
  "https://abc123-8080.app.kvin.wang/node.json",
  "https://def456-8080.app.kvin.wang/node.json"
]
```

Update the `GIST_URL` in the docker-compose.yml to point to your Gist's raw URL, then run `docker compose up -d` on each machine. The containers will automatically generate WireGuard keypairs, discover each other through the Gist, and establish encrypted tunnels.

## Example Output

When the system is working correctly, you'll see log output showing the three-phase connection process:

```
p2pnode  | [peer] fetch https://2a710755cd42e9c0f3fcaf3564471be5acdc3c12-8080.dstack-pha-prod7.phala.network/node.json
p2pnode  | [peer] fetch https://d745076703b1a0b4e2347ad8686e4cff541ce06e-8080.dstack-pha-prod7.phala.network/node.json
p2pnode  | [peer] fetch https://a8d976a85cf3.ngrok-free.app/node.json
p2pnode  | [wg] peer qZrcEJmB at position 0 endpoint 66.220.6.107:59272
p2pnode  | interface: wg0
p2pnode  |   public key: kK3PfytDLs/E7MPJa+hBS3OvAZGGfI0r67wrQmpDxjI=
p2pnode  |   private key: (hidden)
p2pnode  |   listening port: 51820
p2pnode  | 
p2pnode  | peer: zvwUE3ud0SAHlAL0PUrHqiRl3BFeQ8dMxhOon7qjf0w=
p2pnode  |   endpoint: 66.220.6.107:36120
p2pnode  |   allowed ips: 10.88.0.11/32
p2pnode  |   latest handshake: 1 minute, 31 seconds ago
p2pnode  |   transfer: 11.22 KiB received, 12.14 KiB sent
p2pnode  |   persistent keepalive: every 25 seconds
p2pnode  | 
p2pnode  | peer: qZrcEJmB53y1j1+XFJ2DUfGCYtPJclAt+2lCcAqfHkM=
p2pnode  |   endpoint: 66.220.6.107:59272
p2pnode  |   allowed ips: 10.88.0.10/32
p2pnode  |   transfer: 0 B received, 148 B sent
p2pnode  |   persistent keepalive: every 25 seconds
p2pnode  | [wg] traffic rx=11492B tx=12432B
p2pnode  | [http] connected to 10.88.0.10: {'wg_ip': '10.88.0.10/32', 'time': '2025-08-24T21:10:01.999712+00:00'}
p2pnode  | [http] connected to 10.88.0.11: {'wg_ip': '10.88.0.11/32', 'time': '2025-08-24T21:10:02.159579+00:00'}
p2pnode  | [http] serving request from 10.88.0.11
p2pnode  | [http] serving request from 10.88.0.10
p2pnode  | [wg] traffic rx=12836B tx=13776B
```

This output demonstrates all three phases working successfully: peer discovery through HTTPS endpoints, WireGuard tunnel establishment with UDP hole punching (note the external endpoints at 66.220.6.107), and active connectivity testing between nodes on the overlay network (10.88.0.x addresses).

## Limitations and Future Work

This implementation works reliably with full cone NATs, where the external port mapping remains consistent across different destinations. Symmetric NATs and restricted cone NATs may prevent successful hole punching, requiring fallback relay servers or more sophisticated traversal techniques.

The current Gist-based coordination is a stepping stone toward the project's ultimate vision of smart contract-based peer discovery, which would align with dstack's broader architecture of on-chain key management and decentralized infrastructure coordination.
