#!/usr/bin/env python3

import argparse
import json
import socket
import struct
import time
import threading
import requests
# No longer need urllib3 for HTTPS warnings since we're using HTTP

def stun_discover_with_socket(sock):
    sock.settimeout(10)
    stun_request = b'\x00\x01\x00\x00\x21\x12\xa4\x42' + b'\x00' * 12
    sock.bind(('0.0.0.0',41000))
    sock.sendto(stun_request, ('stun.l.google.com', 19302))
    data, addr = sock.recvfrom(1024)
    sock.settimeout(None)
    msg_type = struct.unpack('!H', data[0:2])[0]
    if msg_type == 0x0101:
        offset = 20
        while offset < len(data):
            if offset + 4 > len(data): break
            attr_type = struct.unpack('!H', data[offset:offset+2])[0]
            attr_length = struct.unpack('!H', data[offset+2:offset+4])[0]
            if attr_type == 0x0020 and attr_length >= 8 and offset + 8 <= len(data):
                family = struct.unpack('!B', data[offset+5:offset+6])[0]
                if family == 0x01:
                    xor_port = struct.unpack('!H', data[offset+6:offset+8])[0]
                    port = xor_port ^ 0x2112
                    xor_ip_bytes = data[offset+8:offset+12]
                    magic_cookie = b'\x21\x12\xa4\x42'
                    ip_bytes = bytes(b ^ magic_cookie[i] for i, b in enumerate(xor_ip_bytes))
                    ip = '.'.join(str(b) for b in ip_bytes)
                    return ip, port
            offset += 4 + ((attr_length + 3) // 4) * 4
    return None, None

class HolePunchClient:
    def __init__(self, coord_url):
        self.coord_url = coord_url
        self.client_id = f"client_{int(time.time())}"
        self.udp_socket = None
        self.running = False
        self.hole_punched = False

    def setup_udp_socket(self):
        """Setup UDP socket"""
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def get_echo_service(self):
        """Get echo service address"""
        service_url = f"{self.coord_url}/get_echo_service"
        
        # Get our external IP and port via STUN for hole punch coordination
        external_ip, external_port = stun_discover_with_socket(self.udp_socket)
        if not external_ip or not external_port:
            raise Exception("STUN discovery failed - cannot register without external endpoint")

        print(f"Client discovered external endpoint: {external_ip}:{external_port}")
        
        try:
            response = requests.post(
                service_url,
                json={'client_ip': external_ip, 'client_port': external_port},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print("Got echo service address")
                return result.get('udp_service')
            else:
                print(f"Service request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Failed to get service: {e}")
            return None
    
    def send_punch_packets(self, target_ip, target_port, duration=5):
        """Send UDP packets to target to establish NAT hole"""
        print(f"Sending punch packets to {target_ip}:{target_port} for {duration}s")
        
        packet_count = 0
        end_time = time.time() + duration
        while time.time() < end_time and self.running and not self.hole_punched:
            try:
                message = f"PUNCH from client {self.client_id} at {time.time()}"
                self.udp_socket.sendto(message.encode(), (target_ip, target_port))
                packet_count += 1
                time.sleep(2.0)
            except Exception as e:
                print(f"Punch packet error: {e}")
        
        if self.hole_punched:
            print(f"Hole punch confirmed after {packet_count} packets - stopping punch packets")
        else:
            print(f"Finished sending {packet_count} punch packets")
    
    def listen_for_responses(self):
        """Listen for incoming UDP packets"""
        print("Listening for UDP responses...")
        self.udp_socket.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode()
                print(f"Received from {addr}: {message}")
                
                if "ECHO:" in message:
                    if not self.hole_punched:
                        self.hole_punched = True
                        print("✓ Hole punch successful! UDP echo working.")
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP receive error: {e}")
    
    def test_echo_service(self, target_ip, target_port):
        """Test the echo service after hole punch"""
        print(f"Testing echo service at {target_ip}:{target_port}")
        
        for i in range(5):
            try:
                test_message = f"Hello from {self.client_id}, message {i+1}"
                self.udp_socket.sendto(test_message.encode(), (target_ip, target_port))
                time.sleep(1)
            except Exception as e:
                print(f"Echo test error: {e}")
    
    def run(self):
        """Main client execution"""
        print(f"Starting hole punch client: {self.client_id}")
        
        # Setup UDP socket first
        self.setup_udp_socket()
        
        # Get echo service address
        udp_service = self.get_echo_service()
        if not udp_service:
            return

        
        target_ip = udp_service['ip']
        target_port = udp_service['port']
        
        print(f"Target UDP service: {target_ip}:{target_port}")
        
        # Start listening for responses
        self.running = True
        listen_thread = threading.Thread(target=self.listen_for_responses, daemon=True)
        listen_thread.start()
        
        # Send punch packets
        punch_thread = threading.Thread(
            target=self.send_punch_packets,
            args=(target_ip, target_port),
            daemon=True
        )
        punch_thread.start()
        
        # Wait for hole punch to establish
        time.sleep(5)
        
        # Test echo service
        self.test_echo_service(target_ip, target_port)
        
        # Keep running for a bit to see responses
        time.sleep(10)
        
        self.running = False
        print("Client finished")

def main():
    parser = argparse.ArgumentParser(description='UDP Hole Punch Client')
    parser.add_argument('--coord', required=True, help='Coordinator HTTP URL')
    
    args = parser.parse_args()
    
    client = HolePunchClient(args.coord)
    client.run()

if __name__ == '__main__':
    main()
