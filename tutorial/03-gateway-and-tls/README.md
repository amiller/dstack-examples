# Tutorial 03: Connecting to TEE Nodes

Multiple ways to route traffic to your dstack applications.

## Overview

dstack apps run in isolated TEE environments without public IPs. This tutorial covers three approaches to connect:

| Approach | Use Case | Client Setup |
|----------|----------|--------------|
| Gateway Domain | HTTP/HTTPS apps | None (browser works) |
| Stunnel | TCP protocols (games, SSH) | Install stunnel on client |
| Ngrok | Bypass gateway, public IP | Run ngrok inside TEE |

## Approach 1: Gateway Domain (Default)

Every deployed app gets a URL like:
```
https://<app-id>-<port>.dstack-prod5.phala.network
```

The gateway terminates TLS and routes traffic to your container's port.

```
┌──────────┐     HTTPS      ┌─────────────┐     TCP      ┌──────────┐
│  Client  │ ────────────── │   Gateway   │ ──────────── │ TEE App  │
│ (browser)│                │  (port 443) │              │ (port X) │
└──────────┘                └─────────────┘              └──────────┘
```

**Pros:** Works out of the box, no client setup
**Cons:** HTTP/WebSocket only, gateway sees plaintext

### Example

Deploy any HTTP app:

```yaml
services:
  web:
    image: nginx
    ports:
      - "80:80"
```

After deploy, access at `https://<app-id>-80.dstack-prod5.phala.network`

## Approach 2: Stunnel (TCP over TLS)

For protocols that aren't HTTP - games, SSH, databases, etc. The client runs stunnel to unwrap TLS locally.

```
┌──────────┐   TCP   ┌─────────┐   TLS    ┌─────────────┐  TCP  ┌──────────┐
│ Game     │ ─────── │ stunnel │ ──────── │   Gateway   │ ───── │ TEE App  │
│ Client   │  :25565 │ (local) │          │  (port 443) │       │  :25565  │
└──────────┘         └─────────┘          └─────────────┘       └──────────┘
```

**Pros:** Any TCP protocol works
**Cons:** Requires client-side setup

### Minecraft Example

Server side (in TEE):
```yaml
services:
  minecraft:
    image: itzg/minecraft-server
    environment:
      - EULA=TRUE
    ports:
      - "25565:25565"
```

Client side - create `stunnel.conf`:
```ini
foreground = yes
pid = ./stunnel.pid

[minecraft]
client = yes
accept = 127.0.0.1:25565
connect = <app-id>-25565.dstack-prod5.phala.network:443
```

Run stunnel and connect your Minecraft client to `localhost:25565`:
```bash
stunnel stunnel.conf
```

### SSH Example

Using socat instead of stunnel (simpler one-liner):
```bash
socat TCP-LISTEN:2222,fork,reuseaddr \
  OPENSSL:<app-id>-22.dstack-prod5.phala.network:443
```

Or configure `~/.ssh/config`:
```
Host tee-box
    ProxyCommand openssl s_client -quiet -connect <app-id>-22.dstack-prod5.phala.network:443
    User root
```

Then: `ssh tee-box`

> **macOS note:** System openssl is LibreSSL. Install OpenSSL via homebrew: `brew install openssl`

## Approach 3: Ngrok Reverse Proxy

Run ngrok inside the TEE to get a public URL that bypasses the dstack gateway entirely. Useful when:
- You need a non-TLS public endpoint
- You want to control your own domain
- You're building a reverse tunnel

```
┌──────────┐           ┌─────────────┐   tunnel   ┌──────────┐
│  Client  │ ───────── │ ngrok edge  │ ────────── │ TEE App  │
│          │  public   │  (ngrok.io) │            │ + ngrok  │
└──────────┘   URL     └─────────────┘            └──────────┘
```

**Pros:** Public IP, custom domains, bypasses gateway
**Cons:** Trusts ngrok infrastructure, requires account

### Example

```yaml
services:
  app:
    image: nginx
    ports:
      - "80:80"

  ngrok:
    image: ngrok/ngrok:alpine
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    command: http app:80
    depends_on:
      - app
```

Deploy with your ngrok auth token:
```bash
NGROK_AUTHTOKEN=<your-token> phala deploy ...
```

The ngrok container logs will show your public URL.

### Alternative: Cloudflare Tunnel

Similar concept using Cloudflare:
```yaml
services:
  app:
    image: nginx
    ports:
      - "80:80"

  tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run --token ${CF_TUNNEL_TOKEN}
    depends_on:
      - app
```

## Trust Considerations

| Approach | Who sees plaintext? | Who can intercept? |
|----------|--------------------|--------------------|
| Gateway | dstack gateway | Gateway operator |
| Stunnel | dstack gateway | Gateway operator |
| Ngrok | ngrok servers | Ngrok |
| CF Tunnel | Cloudflare | Cloudflare |

For end-to-end encryption where only the TEE sees plaintext, you need:
- TLS termination inside the TEE (see [05-hardening-https](../05-hardening-https))
- Custom domain with cert inside TEE (see `dstack-ingress`)

## Files

```
03-gateway-and-tls/
├── docker-compose.yaml        # TCP echo server for stunnel testing
├── docker-compose-ngrok.yaml  # Ngrok reverse proxy example
├── stunnel-client.conf        # Client-side stunnel config template
└── README.md
```

## Next Steps

- [04-onchain-oracle](../04-onchain-oracle): On-chain verification with AppAuth
- [05-hardening-https](../05-hardening-https): TLS inside TEE with OCSP/CT verification

## References

- [tcp-port-forwarding](../../tcp-port-forwarding): More socat examples
- [ssh-over-gateway](../../ssh-over-gateway): SSH server setup
- [minecraft](../../minecraft): Full minecraft example
