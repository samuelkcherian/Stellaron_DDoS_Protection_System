# security_tool/debug_tool.py

import time
from collections import defaultdict

LOG_FILE_PATH = "../logs/access.log"
TIME_WINDOW = 10
REQUEST_LIMIT = 20

request_counts = defaultdict(list)

print("--- Starting Debug Tool ---")

try:
    with open(LOG_FILE_PATH, "r") as f:
        log_lines = f.readlines()
except FileNotFoundError:
    print(f"❌ ERROR: Log file not found at {LOG_FILE_PATH}")
    print("Please run the attack for a few seconds first to generate the log file.")
    exit()

if not log_lines:
    print("Log file is empty. No traffic to analyze.")
    exit()

print(f"Found {len(log_lines)} lines in the log file. Analyzing...")

# --- This is the same detection logic from the main tool ---
for line in log_lines:
    try:
        ip_address = line.split()[0]
        current_time = time.time()
        
        request_counts[ip_address].append(current_time)
        request_counts[ip_address] = [
            t for t in request_counts[ip_address] if current_time - t < TIME_WINDOW
        ]
        
        if len(request_counts[ip_address]) > REQUEST_LIMIT:
            print(f"✅ SUCCESS: Attack detected from IP: {ip_address}")
            print(f"   -> Saw {len(request_counts[ip_address])} requests in the time window.")
            exit() # Exit after first detection
            
    except IndexError:
        continue # Ignore malformed lines

print("\n--- Analysis Complete ---")
print("No attack was detected based on the current rules.")
print("IPs found in the log file:")
for ip, timestamps in request_counts.items():
    print(f"  - IP: {ip}, Request Count: {len(timestamps)}")