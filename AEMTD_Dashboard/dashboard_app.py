from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Store alerts in memory (for this simple example)
alerts = []

@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('dashboard.html', alerts=alerts)

@app.route('/alert', methods=['POST'])
def receive_alert():
    """An API endpoint to receive alerts from the Java proxy."""
    data = request.json
    print(f"Received alert: {data}")
    
    alert = {
        "reason": data.get("reason", "Unknown"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    alerts.insert(0, alert) # Add to the top of the list
    
    return jsonify({"status": "success", "message": "Alert received"})

if __name__ == '__main__':
    # Run on port 8888 to avoid conflicts
    app.run(host='0.0.0.0', port=8888)