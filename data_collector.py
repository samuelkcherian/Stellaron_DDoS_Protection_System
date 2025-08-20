# DDoS_Protection_tool/data_collector.py

import csv
import time
from scapy.all import *
from collections import defaultdict
import threading

# --- Configuration ---
CSV_FILE_PATH = 'ddos_dataset.csv'
CAPTURE_INTERFACE = "any"  # Use "any" on Linux, or find your specific interface (e.g., "eth0", "en0")
TIME_WINDOW = 5  # Aggregate features over a 5-second window

# --- Feature Extraction Globals ---
# These dictionaries will store aggregated data for each source IP
packet_counts = defaultdict(int)
packet_sizes = defaultdict(int)
syn_counts = defaultdict(int)
ack_counts = defaultdict(int)
fin_counts = defaultdict(int)
first_packet_time = {}
last_packet_time = {}

# Thread-safe lock
lock = threading.Lock()

def write_header():
    """Writes the header row to the CSV file if it doesn't exist."""
    try:
        with open(CSV_FILE_PATH, 'x', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = [
                'src_ip',
                'flow_duration',      # Time between first and last packet
                'total_packets',      # Total packets in flow
                'avg_packet_size',    # Average packet size
                'syn_flag_count',     # Number of packets with SYN flag
                'ack_flag_count',     # Number of packets with ACK flag
                'fin_flag_count',     # Number of packets with FIN flag
                'packets_per_second', # Packets per second
                'label'               # 0 for normal, 1 for attack
            ]
            writer.writerow(header)
    except FileExistsError:
        pass # File already exists

def process_packet(packet):
    """Callback function to process each captured packet."""
    if IP in packet and TCP in packet:
        with lock:
            src_ip = packet[IP].src
            
            # Update packet counts and sizes
            packet_counts[src_ip] += 1
            packet_sizes[src_ip] += len(packet)
            
            # Update timestamps
            current_time = time.time()
            if src_ip not in first_packet_time:
                first_packet_time[src_ip] = current_time
            last_packet_time[src_ip] = current_time
            
            # Update TCP flag counts
            flags = packet[TCP].flags
            if flags & 0x02:  # SYN flag
                syn_counts[src_ip] += 1
            if flags & 0x10:  # ACK flag
                ack_counts[src_ip] += 1
            if flags & 0x01:  # FIN flag
                fin_counts[src_ip] += 1

def aggregate_and_write(label):
    """Periodically aggregates features and writes them to the CSV."""
    while True:
        time.sleep(TIME_WINDOW)
        with lock:
            # Create a copy to avoid issues with dictionary size changing during iteration
            current_ips = list(packet_counts.keys())
            
            with open(CSV_FILE_PATH, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for src_ip in current_ips:
                    # Calculate flow duration
                    duration = last_packet_time[src_ip] - first_packet_time[src_ip]
                    if duration == 0:
                        duration = 1 # Avoid division by zero
                    
                    # Calculate derived features
                    total_packets = packet_counts[src_ip]
                    avg_size = packet_sizes[src_ip] / total_packets if total_packets > 0 else 0
                    pps = total_packets / duration
                    
                    # Prepare row
                    row = [
                        src_ip,
                        f"{duration:.6f}",
                        total_packets,
                        f"{avg_size:.2f}",
                        syn_counts[src_ip],
                        ack_counts[src_ip],
                        fin_counts[src_ip],
                        f"{pps:.2f}",
                        label
                    ]
                    writer.writerow(row)
            
            # Reset dictionaries for the next window
            packet_counts.clear()
            packet_sizes.clear()
            syn_counts.clear()
            ack_counts.clear()
            fin_counts.clear()
            first_packet_time.clear()
            last_packet_time.clear()

if __name__ == '__main__':
    label_choice = input("Enter '0' for NORMAL traffic or '1' for ATTACK traffic: ")
    if label_choice not in ['0', '1']:
        print("Invalid choice. Exiting.")
        exit()
        
    write_header()
    
    # Start the aggregation thread
    aggregator_thread = threading.Thread(target=aggregate_and_write, args=(label_choice,))
    aggregator_thread.daemon = True
    aggregator_thread.start()

    print(f"Starting packet capture on interface '{CAPTURE_INTERFACE}'. Press Ctrl+C to stop.")
    try:
        sniff(iface=CAPTURE_tINTERFACE, prn=process_packet, store=0)
    except Exception as e:
        print(f"Error starting sniffer: {e}")
        print("Please ensure you are running this script with root/administrator privileges.")
        print("And that the interface name is correct.")