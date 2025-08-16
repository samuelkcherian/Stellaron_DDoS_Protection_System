# security_tool/main_tool.py (Complete Final Version)

import time
import subprocess
import os
import threading
import sqlite3
import bcrypt
from collections import defaultdict, deque, Counter
from flask import Flask, jsonify, request
from flask_cors import CORS
import traceback
from datetime import datetime

# --- Security Configuration ---
security_config = {
    "TIME_WINDOW": 10, "REQUEST_LIMIT": 20, "GLOBAL_REQUEST_LIMIT": 1000,
    "GLOBAL_TIME_WINDOW": 10, "UNBLOCK_DURATION": 300, "ANOMALY_THRESHOLD_MULTIPLIER": 5
}

# --- Database and File Paths ---
DATABASE_PATH = 'users.db'
LOG_FILE_PATH = "../logs/access.log"
BLOCKLIST_FILE_PATH = "../nginx/blocklist.conf"
POLL_INTERVAL = 2
API_PORT = 5001

# --- In-memory data stores ---
request_counts = defaultdict(list)
path_counts = defaultdict(list)
user_agent_counts = defaultdict(list)
hourly_traffic = defaultdict(int)
blocked_ips = {}
recent_log_entries = deque(maxlen=100)
global_request_timestamps = deque(maxlen=2000)
traffic_summary = deque(maxlen=60)
security_alerts = deque(maxlen=200)
block_history = deque(maxlen=1000)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT)''')
    conn.commit(); conn.close()
    print("Database initialized.")

# --- Alert Logging ---
def log_alert(alert_type, details, level='High'):
    alert = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": alert_type, "details": details, "level": level}
    security_alerts.appendleft(alert)
    print(f"ALERT LOGGED: {alert}")

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---
@app.route('/api/register', methods=['POST'])
def register_user():
    data=request.get_json(); name,email,password=data.get('name'),data.get('email'),data.get('password')
    if not all([name,email,password]): return jsonify({"status":"error","message":"Missing fields"}), 400
    hashed=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
    try:
        conn=sqlite3.connect(DATABASE_PATH); cursor=conn.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",(name,email,hashed))
        conn.commit(); conn.close()
        return jsonify({"status":"success","message":"User registered"}), 201
    except sqlite3.IntegrityError: return jsonify({"status":"error","message":"Email exists"}), 409

@app.route('/api/login', methods=['POST'])
def login_user():
    data=request.get_json(); email,password=data.get('email'),data.get('password')
    if not all([email,password]): return jsonify({"status":"error","message":"Missing fields"}), 400
    conn=sqlite3.connect(DATABASE_PATH); cursor=conn.cursor()
    cursor.execute("SELECT name,password FROM users WHERE email=?",(email,))
    user=cursor.fetchone(); conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'),user[1]):
        return jsonify({"status":"success","message":"Login successful","name":user[0]}), 200
    else: return jsonify({"status":"error","message":"Invalid credentials"}), 401

@app.route('/api/report_l4_block', methods=['POST'])
def report_l4_block():
    ip=request.get_json().get('ip')
    if ip and ip not in blocked_ips:
        log_alert("SYN Flood (L4)",f"IP: {ip}","Critical"); blocked_ips[ip]=time.time(); block_history.append(ip)
        return jsonify({"status":"success"}), 200
    return jsonify({"status":"ignored"}), 200

@app.route('/api/settings', methods=['GET'])
def get_settings(): return jsonify(security_config)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data=request.get_json()
    try:
        for key in security_config: security_config[key]=int(data.get(key,security_config[key]))
        log_alert("Config Update","Settings updated","Info")
        return jsonify({"status":"success"})
    except(ValueError,TypeError): return jsonify({"status":"error","message":"Invalid data"}), 400

@app.route('/api/blocked_ips')
def get_blocked_ips(): return jsonify(list(blocked_ips.keys()))

@app.route('/api/live_traffic')
def get_live_traffic(): return jsonify(list(recent_log_entries))

@app.route('/api/traffic_summary')
def get_traffic_summary():
    labels=[f"T-{(len(traffic_summary)-i-1)*POLL_INTERVAL}s" for i in range(len(traffic_summary))]
    return jsonify({"labels":labels,"data":list(traffic_summary)})

@app.route('/api/alerts')
def get_alerts(): return jsonify(list(security_alerts))

@app.route('/api/reporting_summary')
def get_reporting_summary():
    top_attackers = Counter(block_history).most_common(10)
    alerts_by_type = Counter(alert['type'] for alert in security_alerts)
    summary = {
        "top_attackers": [{"ip": ip, "count": count} for ip, count in top_attackers],
        "alerts_by_type": dict(alerts_by_type)
    }
    return jsonify(summary)

# --- AEMTD Integration ---
@app.route('/api/aemtd-alert', methods=['POST'])
def receive_aemtd_alert():
    """Receives an alert from the AEMTD Java proxy."""
    data = request.json
    details = data.get("reason", "AEMTD Threat Detected")
    source_ip = request.remote_addr

    print(f"Received AEMTD alert from {source_ip}: {details}")

    # Add the alert to your existing alert system
    alerts.insert(0, {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "level": "critical", # AEMTD alerts are always critical
        "type": "AEMTD Anomaly",
        "details": f"{details} (Source: AEMTD Proxy)"
    })
    return jsonify({"status": "success", "message": "AEMTD alert received"})
# --- End of AEMTD Integration ---

def run_api():
    app.run(host='0.0.0.0', port=API_PORT)

# --- Core Logic ---
def process_log_entry(line):
    current_time=time.time()
    hour_key=time.strftime("%Y-%m-%d-%H",time.gmtime(current_time))
    hourly_traffic[hour_key]+=1
    recent_log_entries.append(line.strip())
    global_request_timestamps.append(current_time)
    try:
        ip,path,agent=line.split()[0],line.split('"')[1].split()[1],line.split('"')[5]
    except IndexError: return
    if len(global_request_timestamps)>security_config["GLOBAL_REQUEST_LIMIT"]:
        log_alert("Volumetric Anomaly",f"Global traffic > {security_config['GLOBAL_REQUEST_LIMIT']} reqs","Medium")
    if ip in blocked_ips: return
    request_counts[ip].append(current_time)
    request_counts[ip]=[t for t in request_counts[ip] if current_time-t<security_config["TIME_WINDOW"]]
    if len(request_counts[ip])>security_config["REQUEST_LIMIT"]:
        log_alert("High-Rate Attack (L7)",f"IP: {ip}","High"); block_ip(ip); return
    path_counts[path].append(current_time)
    path_counts[path]=[t for t in path_counts[path] if current_time-t<security_config["TIME_WINDOW"]]
    if len(path_counts[path])>(security_config["REQUEST_LIMIT"]*2):
        log_alert("Path Surge",f"Path: {path}","Medium")
    user_agent_counts[agent].append(current_time)
    user_agent_counts[agent]=[t for t in user_agent_counts[agent] if current_time-t<security_config["TIME_WINDOW"]]
    if len(user_agent_counts[agent])>(security_config["REQUEST_LIMIT"]*5):
        log_alert("Bot-like Behavior",f"User-Agent: {agent}","Medium")

def block_ip(ip):
    if ip in blocked_ips: return
    blocked_ips[ip]=time.time()
    block_history.append(ip)
    with open(BLOCKLIST_FILE_PATH,"a") as f: f.write(f"deny {ip};\n")
    print(f"☁️ SIMULATING: Blocking {ip} in AWS WAF...")

def unblock_expired_ips():
    current_time=time.time()
    unblocked=[ip for ip,block_time in blocked_ips.items() if current_time-block_time>security_config["UNBLOCK_DURATION"]]
    if not unblocked: return
    log_alert("IP Unblocked",f"IPs: {', '.join(unblocked)}","Info")
    for ip in unblocked: del blocked_ips[ip]
    with open(BLOCKLIST_FILE_PATH,"w") as f:
        for ip in blocked_ips: f.write(f"deny {ip};\n")
    print("☁️ SIMULATING: Unblocking expired IPs in AWS WAF...")

def check_for_time_anomalies():
    now = time.time()
    current_hour_key = time.strftime("%Y-%m-%d-%H", time.gmtime(now))
    if len(hourly_traffic) < 2: return
    previous_hours_traffic = [count for key, count in hourly_traffic.items() if key != current_hour_key]
    if not previous_hours_traffic: return
    average_traffic = sum(previous_hours_traffic) / len(previous_hours_traffic)
    current_traffic = hourly_traffic.get(current_hour_key, 0)
    if average_traffic > 50 and current_traffic > (average_traffic * security_config["ANOMALY_THRESHOLD_MULTIPLIER"]):
        log_alert("Time-Based Anomaly", f"Current traffic ({current_traffic}) is >{security_config['ANOMALY_THRESHOLD_MULTIPLIER']}x the average ({average_traffic:.0f})", "Critical")

def watch_log_file(log_path,last_pos):
    count=0
    try:
        with open(log_path,"r") as f:
            f.seek(last_pos)
            for line in f.readlines():
                if line.strip(): process_log_entry(line); count+=1
            return f.tell(),count
    except FileNotFoundError: return last_pos,0
    except Exception: traceback.print_exc(); return last_pos,0

if __name__=="__main__":
    init_db()
    print("🚀 Starting DDoS Protection Tool...")
    api_thread=threading.Thread(target=run_api,daemon=True); api_thread.start()
    print(f"📊 Dashboard API running on http://localhost:{API_PORT}")
    if os.path.exists(BLOCKLIST_FILE_PATH):
        with open(BLOCKLIST_FILE_PATH,"r") as f:
            for line in f:
                if "deny" in line: blocked_ips[line.split()[1].replace(';','')]=time.time()
    print(f"Loaded {len(blocked_ips)} previously blocked IPs.")
    try: last_known_pos=os.path.getsize(LOG_FILE_PATH)
    except FileNotFoundError: last_known_pos = 0
    print(f"👀 Watching log file: {LOG_FILE_PATH}...")
    last_anomaly_check = time.time()
    try:
        while True:
            last_known_pos,new_requests=watch_log_file(LOG_FILE_PATH,last_known_pos)
            traffic_summary.append(new_requests)
            unblock_expired_ips()
            if time.time() - last_anomaly_check > 60:
                check_for_time_anomalies()
                last_anomaly_check = time.time()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt: 
        print("\n🛑 Tool stopped.")
