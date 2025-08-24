#!/usr/bin/env python3
import stun
import sys

servers=['stun.l.google.com','stun1.l.google.com','stun.cloudflare.com','stun.nextcloud.com','stun.ekiga.net']
port=int(sys.argv[1])if len(sys.argv)>1 else 12345
results=[]

for s in servers:
    try:
        stun.STUN_SERVERS=[(s,19302 if 'google'in s else 3478)]
        _,ip,p=stun.get_ip_info(source_port=port)
        if ip and p:
            r=f"{ip}:{p}"
            results.append(r)
            print(f"✓ {s}: {r}")
        else:print(f"❌ {s}: no result")
    except Exception as e:print(f"❌ {s}: {e}")

u=set(results)
print(f"\n{'✅ CONSISTENT!'if len(u)==1 else'⚠️ INCONSISTENT!'} {len(results)} results, {len(u)} unique: {list(u)}")