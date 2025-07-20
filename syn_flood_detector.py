# syn_flood_detector.py (Complete Final Version)

import time
import subprocess
import requests
from collections import defaultdict
from scapy.all import sniff, TCP, IP

# --- IMPORTANT: CONFIGURE THIS ---
# Replace this with the actual local network IP of the computer running the main tool
MAIN_TOOL_API_URL = "http://192.168.1.3:5001/api/report_l4_block"
# --------------------------------

print("🚀 Starting SYN Flood Detector...")
print("NOTE: This script must be run with administrator/root privileges (sudo).")

# --- Configuration ---
TIME_WINDOW = 5  # seconds
SYN_PACKET_LIMIT = 20 # a burst of 20 SYN packets in 5 seconds
blocked_ips = set()

# In-memory data store
syn_counts = defaultdict(list)

def block_ip_with_iptables(ip_address):
    """Blocks an IP address using the system's iptables firewall and reports it."""
    if ip_address in blocked_ips:
        return
    
    print(f"🔥 Blocking {ip_address} at the firewall level using iptables...")
    try:
        # The script is run with sudo, so we call iptables directly.
        subprocess.run(
            ["iptables", "-A", "INPUT", "-s", ip_address, "-j", "DROP"],
            check=True
        )
        blocked_ips.add(ip_address)
        print(f"✅ Firewall rule added. IP {ip_address} is now blocked.")

        # Report the blocked IP to the main dashboard API
        try:
            print(f"📞 Reporting {ip_address} to the main dashboard...")
            requests.post(MAIN_TOOL_API_URL, json={"ip": ip_address}, timeout=3)
        except Exception as e:
            print(f"    - Could not report to dashboard API: {e}")

    except FileNotFoundError:
        print("❌ 'iptables' command not found. Make sure it is installed.")
    except Exception as e:
        print(f"❌ Failed to add iptables rule: {e}")


def packet_callback(packet):
    """This function is called for every packet captured."""
    # Check that the packet has both an IP and a TCP layer and is a SYN packet
    if IP in packet and TCP in packet and packet[TCP].flags == 'S':
        # Get the source IP address from the IP layer
        src_ip = packet[IP].src
        
        if src_ip in blocked_ips:
            return

        current_time = time.time()
        
        # Add current request timestamp and clean up old ones
        syn_counts[src_ip].append(current_time)
        syn_counts[src_ip] = [t for t in syn_counts[src_ip] if current_time - t < TIME_WINDOW]

        # If the count exceeds the limit, it's a flood
        if len(syn_counts[src_ip]) > SYN_PACKET_LIMIT:
            print(f"🚨🚨🚨 SYN FLOOD DETECTED from IP: {src_ip} 🚨🚨🚨")
            block_ip_with_iptables(src_ip)
            # Clear the history for this IP to prevent constant re-blocking alerts
            del syn_counts[src_ip]

if __name__ == "__main__":
    try:
        print("Sniffing network traffic... Press Ctrl+C to stop.")
        # Sniff all network traffic and call packet_callback for each packet
        sniff(prn=packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n🛑 Detector stopped.")
    except Exception as e:
        print(f"An error occurred: {e}. Please ensure you are running with sudo/administrator privileges.")