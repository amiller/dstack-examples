#!/usr/bin/env python3
"""
Minimal STUN client to discover external IP:port
Usage: python3 stun_test.py [--port LOCAL_PORT]
"""

import argparse
import socket
import struct

def stun_discover(local_port=None):
    """Discover external IP:port using STUN"""
    stun_servers = [
        ('stun.l.google.com', 19302),
        ('stun1.l.google.com', 19302),
        ('stun.cloudflare.com', 3478),
    ]
    
    for stun_host, stun_port in stun_servers:
        try:
            print(f"Trying STUN server: {stun_host}:{stun_port}")
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # Bind to specific local port if requested
            if local_port:
                sock.bind(('0.0.0.0', local_port))
                print(f"Bound to local port: {local_port}")
            
            # Minimal STUN binding request
            # Message type: 0x0001 (Binding Request)
            # Message length: 0x0000 (no attributes)
            # Magic cookie: 0x2112a442
            # Transaction ID: 12 bytes (zeros for simplicity)
            stun_request = b'\x00\x01\x00\x00\x21\x12\xa4\x42' + b'\x00' * 12
            
            # Send STUN request
            sock.sendto(stun_request, (stun_host, stun_port))
            
            # Receive response
            data, addr = sock.recvfrom(1024)
            sock.close()
            
            print(f"Received {len(data)} bytes from {addr}")
            
            # Parse STUN response
            if len(data) < 20:
                print("Response too short")
                continue
                
            # Check if it's a binding response (0x0101)
            msg_type = struct.unpack('!H', data[0:2])[0]
            if msg_type != 0x0101:
                print(f"Unexpected message type: 0x{msg_type:04x}")
                continue
                
            print("Valid STUN binding response received")
            
            # Parse attributes starting at offset 20
            offset = 20
            while offset < len(data):
                if offset + 4 > len(data):
                    break
                    
                attr_type = struct.unpack('!H', data[offset:offset+2])[0]
                attr_length = struct.unpack('!H', data[offset+2:offset+4])[0]
                
                print(f"Attribute: type=0x{attr_type:04x}, length={attr_length}")
                
                if attr_type == 0x0001:  # MAPPED-ADDRESS
                    if attr_length >= 8 and offset + 8 <= len(data):
                        # Skip reserved byte
                        family = struct.unpack('!B', data[offset+5:offset+6])[0]
                        if family == 0x01:  # IPv4
                            port = struct.unpack('!H', data[offset+6:offset+8])[0]
                            ip_bytes = data[offset+8:offset+12]
                            ip = '.'.join(str(b) for b in ip_bytes)
                            print(f"✓ MAPPED-ADDRESS: {ip}:{port}")
                            return ip, port
                            
                elif attr_type == 0x0020:  # XOR-MAPPED-ADDRESS  
                    if attr_length >= 8 and offset + 8 <= len(data):
                        # Skip reserved byte
                        family = struct.unpack('!B', data[offset+5:offset+6])[0]
                        if family == 0x01:  # IPv4
                            # XOR with magic cookie for XOR-MAPPED-ADDRESS
                            xor_port = struct.unpack('!H', data[offset+6:offset+8])[0]
                            port = xor_port ^ 0x2112  # XOR with first 2 bytes of magic cookie
                            
                            xor_ip_bytes = data[offset+8:offset+12]
                            magic_cookie = b'\x21\x12\xa4\x42'
                            ip_bytes = bytes(b ^ magic_cookie[i] for i, b in enumerate(xor_ip_bytes))
                            ip = '.'.join(str(b) for b in ip_bytes)
                            print(f"✓ XOR-MAPPED-ADDRESS: {ip}:{port}")
                            return ip, port
                
                # Move to next attribute (with padding)
                offset += 4 + ((attr_length + 3) // 4) * 4
                
        except Exception as e:
            print(f"Failed with {stun_host}: {e}")
            continue
    
    print("❌ All STUN servers failed")
    return None, None

def main():
    parser = argparse.ArgumentParser(description='Test STUN discovery of external IP:port')
    parser.add_argument('--port', type=int, help='Local UDP port to bind (optional)')
    args = parser.parse_args()
    
    print("🔍 STUN External IP:Port Discovery")
    print("=" * 40)
    
    external_ip, external_port = stun_discover(args.port)
    
    if external_ip and external_port:
        print(f"\n🎯 Your external endpoint: {external_ip}:{external_port}")
        if args.port:
            print(f"   Local port: {args.port} → External port: {external_port}")
    else:
        print("\n❌ Could not discover external endpoint")

if __name__ == '__main__':
    main()