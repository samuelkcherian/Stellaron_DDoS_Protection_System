# Stellaron: Real-Time DDoS Protection Dashboard

A comprehensive, multi-layered security dashboard designed to detect, mitigate, and report on both Layer 7 (Application) and Layer 4 (Network) DDoS attacks in real-time. This project simulates a professional Security Operations Center (SOC) environment with a full-featured web interface.

---

## ✨ Features

* **Multi-Panel SOC Dashboard:** A professional, responsive UI with separate panels for live monitoring, historical alerts, configurable settings, and summary reporting.
* **Real-Time Traffic Analysis:** A live-updating chart visualizes incoming traffic volume, providing immediate insight into network activity.
* **Layer 7 Attack Detection:**
    * **High-Rate Limiting:** Automatically detects and blocks single IPs sending too many requests.
    * **Path Surge Detection:** Identifies targeted attacks on specific API endpoints or pages.
    * **Bot-like Behavior:** Flags suspicious activity based on non-standard User-Agents.
* **Layer 4 Attack Detection:**
    * Includes a standalone network packet sniffer to detect low-level **SYN Floods** that are invisible to web server logs.
* **Integrated Alert System:** All detected threats (from both L4 and L7) are logged and displayed on a unified Alerts panel with severity levels (Info, Medium, High, Critical).
* **Automated Mitigation & Recovery:**
    * Automatically blocks attacker IPs.
    * Automatically unblocks IPs after a configurable duration to ensure service recovery.
* **Dynamic Configuration:** A settings panel allows administrators to change detection thresholds (e.g., request limits, time windows) in real-time without restarting the system.
* **Comprehensive Reporting:** A reporting dashboard provides a high-level summary of security events, including a breakdown of alert types and a "Top 10 Attackers" list.
* **Secure User Authentication:** A complete login and registration system with password hashing (`bcrypt`) protects access to the dashboard.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask (for the API), Gunicorn (for the web server)
* **Frontend:** HTML, CSS, Vanilla JavaScript
* **Data Visualization:** Chart.js
* **Containerization:** Docker & Docker Compose
* **Proxy & Firewall:** Nginx
* **Database:** SQLite (for user management)
* **Network Analysis:** Scapy
* **Password Security:** bcrypt

---

## 🏗️ Cloud-Native Architecture

This project is built as a local simulation of a modern, cloud-native security architecture.

* **Protection:** In a real-world deployment on a cloud like AWS, initial traffic would be filtered by **AWS Shield** (for L3/L4 attacks).
* **Filtering:** The remaining traffic would pass through **AWS WAF (Web Application Firewall)**.
* **Application:** The Docker containers would run on **EC2 instances** within an Auto Scaling Group, managed by an **Elastic Load Balancer (ELB)**.
* **Control Plane:** Our Python security tool acts as the "brains" or control plane. Instead of just updating a local Nginx file, the `block_ip` function would make an API call to the AWS WAF to create a blocking rule at the cloud edge, providing a more robust and scalable defense.

---

## 🚀 How to Run Locally

**Prerequisites:**
* Docker & Docker Compose
* Python 3.x
* (For L4 Detection) A Linux environment (like a Kali VM) with `scapy` and `hping3` installed.

**Setup:**

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Install Python dependencies for the main tool:**
    ```bash
    pip install -r security_tool/requirements.txt
    ```

**Execution (Requires 3-4 Terminals):**

1.  **Terminal 1: Start the Web Application**
    ```bash
    docker compose up --build
    ```

2.  **Terminal 2: Start the Security Tool & API**
    ```bash
    python security_tool/main_tool.py
    ```

3.  **Terminal 3: Start the Frontend Server**
    ```bash
    cd frontend
    python -m http.server 8000
    ```

4.  **Access the Dashboard:**
    * Open your browser to **`http://localhost:8000`**.
    * Register a new user and log in.

5.  **Simulate Attacks:**
    * **Layer 7 (HTTP Flood):** In a new terminal, run `python attack.py`.
    * **Layer 4 (SYN Flood):** Run the detector on your host (`sudo python syn_flood_detector.py`) and the `hping3` attack from your VM.
