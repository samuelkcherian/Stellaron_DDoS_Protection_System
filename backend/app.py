# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# Flask initialization is now much simpler
app = Flask(__name__)
CORS(app) # Allow requests from the frontend

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# --- Your API Endpoints ---

# This endpoint is for AEMTD alerts
@app.route('/api/aemtd-alert', methods=['POST'])
def receive_aemtd_alert():
    data = request.json
    print(f"Received AEMTD alert: {data}")
    # In a real app, you would process this alert
    return jsonify({"status": "success"})

# This is a placeholder for your original log functionality
@app.route('/api/get_logs')
def get_logs():
    return jsonify({"logs": [], "blocked_ips": []})

# The root route is no longer needed in Flask
# because Nginx is serving index.html directly.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)