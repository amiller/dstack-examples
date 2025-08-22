# UDP Hole Punch Demo

This repo demonstrates **bidirectional UDP hole punching** with smart packet management:

- **Server (Docker Compose)**: UDP echo server with HTTP endpoint for service discovery and hole punch coordination
- **Client (standalone script)**: Uses STUN discovery for NAT mapping, automatically stops punch packets when hole punch succeeds

---

## How It Works

1. **Dynamic Socket Management**
   - UDP service: STUN discovery on port 43000 → binds echo service to same port
   - Client: STUN discovery → communicates using discovered external mapping
   - **Key feature**: Automatic socket rebuilding when NAT mappings expire (30s timeout)

2. **Service Discovery** 
   - UDP service discovers external IP:port via STUN on startup

3. **Smart Hole Punch Coordination**
   - Client requests echo service with their external IP:port
   - **Service immediately sends hello packet** to client's external address
   - **Bidirectional hole punch established** instantly

4. **Intelligent Punch Packets**
   - Client sends punch packets until first echo response received
   - **Stops immediately** when hole punch confirmed (no redundant traffic)
   - Transitions to actual message testing

5. **Echo Service**
   - Echoes non-punch messages back to demonstrate successful communication
   - Logs all traffic for debugging

---

## Repo Layout

```
.
├── docker-compose.yml        # Single UDP echo service with HTTP endpoint
├── client.py                # Smart client with socket reuse
└── README.md                # This file
```

---

## Running the Server

```bash
docker compose up
```

This launches the echo service on:
* Port `8080` (HTTP endpoint)
* UDP port (STUN-discovered for echo service)

---

## Running the Client

From another host/network:

```bash
python3 client.py --coord http://<SERVER_PUBLIC_IP>:8080
```

Output shows:
* Service registration and hole punch coordination
* Minimal punch packets (stops when successful)
* Echo test messages and responses

Example output:
```
[Example output will be added here]
```

---

## Key Implementation Details

### Dynamic Socket Management (Critical for NAT Traversal)
- **UDP service**: STUN discovery via `stun.get_ip_info(source_port=43000)` → bind echo service to port 43000 → automatic rebuild on 30s timeout
- **Client**: `stun_discover_with_socket()` on port 41000 → communication using discovered external mapping
- **Why it works**: Immediate bidirectional hole punching establishes connection, socket rebuilding handles NAT mapping expiry

### Smart Punch Packet Management
- Client sends punch packets every 2 seconds until first echo received
- Immediately stops when `hole_punched = True` (typically after 1-2 packets)
- Eliminates redundant traffic once hole punch confirmed

### Single Service Architecture
- Combined HTTP endpoint and UDP echo service in one container
- HTTP endpoint receives client requests with external IP:port
- Immediately sends hello packet to establish bidirectional hole

---

## Testing Results

Typical successful flow:
```
UDP service discovers external IP:port via STUN
Client requests echo service → service sends hello packet → hole punch established
Client sends 1-2 punch packets → receives echo → stops punch packets
Direct UDP communication established between external endpoints
```

Works with **full cone NATs**, **port-restricted cone NATs**, and many **symmetric NATs** due to immediate bidirectional hole punching and socket rebuilding.

