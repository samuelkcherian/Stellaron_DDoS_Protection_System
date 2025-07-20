# attack.py
import requests
import time

print("--- Starting Attack ---")
url = "http://localhost"

while True:
    try:
        # Send a request and ignore the response
        requests.get(url, timeout=0.5)
        print(".", end="", flush=True) # Print a dot for each successful request
    except requests.exceptions.RequestException:
        # This will happen when Nginx blocks the IP
        print("\n❌ Connection Failed. Target is likely blocked or down.")
        time.sleep(2) # Wait a bit before retrying