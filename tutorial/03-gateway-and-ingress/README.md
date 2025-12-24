# Tutorial 03: Gateway and Ingress

Custom domains with automatic SSL for TEE applications.

## Overview

dstack apps get a default domain like `<app-id>-8080.dstack-prod5.phala.network`. For production, you'll want a custom domain with proper TLS certificates.

**dstack-ingress** provides:
- Automatic SSL via Let's Encrypt (DNS validation)
- Multi-domain support
- Certificate evidence generation with TDX quote chain
- CAA records to restrict certificate issuance

## Quick Start

```yaml
services:
  ingress:
    image: dstacktee/dstack-ingress:20250929@sha256:2b47b3e538df0b3e7724255b89369194c8c83a7cfba64d2faf0115ad0a586458
    ports:
      - "443:443"
    environment:
      - DNS_PROVIDER=cloudflare
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
      - DOMAIN=${DOMAIN}
      - GATEWAY_DOMAIN=${GATEWAY_DOMAIN}
      - CERTBOT_EMAIL=${CERTBOT_EMAIL}
      - SET_CAA=true
      - TARGET_ENDPOINT=http://app:80
    volumes:
      - /var/run/dstack.sock:/var/run/dstack.sock
      - cert-data:/etc/letsencrypt

  app:
    image: nginx  # Your app

volumes:
  cert-data:
```

## Full Documentation

See [dstack-ingress](../../custom-domain/dstack-ingress) for:

- Multi-domain configuration
- DNS provider setup (Cloudflare, Linode, Route53)
- gRPC support
- Certificate evidence and verification
- Building from source

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    dstack-ingress                           │
│                                                             │
│  1. Obtains SSL cert from Let's Encrypt (DNS validation)  │
│  2. Creates CNAME → dstack gateway                         │
│  3. Sets CAA record (optional)                             │
│  4. Generates evidence: quote.json with cert hash          │
│  5. Proxies HTTPS → your app                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Certificate Verification

dstack-ingress generates evidence files at `https://your-domain.com/evidences/`:

| File | Contents |
|------|----------|
| `quote.json` | TDX quote with SHA-256 of sha256sum.txt in report_data |
| `sha256sum.txt` | Hashes of acme-account.json and cert.pem |
| `acme-account.json` | ACME credentials (proves cert was requested from TEE) |
| `cert.pem` | Current TLS certificate |

This creates a verification chain: TDX quote → file hashes → certificate.

## When to Use

| Scenario | Solution |
|----------|----------|
| Development/testing | Default gateway domain (no setup) |
| Production with custom domain | dstack-ingress |
| Multiple domains per app | dstack-ingress multi-domain mode |

## Next Steps

- [01-attestation-oracle](../01-attestation-oracle): Build verifiable apps
- [02-persistence-and-kms](../02-persistence-and-kms): Persistent keys

## References

- [dstack-ingress README](../../custom-domain/dstack-ingress/README.md)
- [DNS Provider Configuration](../../custom-domain/dstack-ingress/DNS_PROVIDERS.md)
