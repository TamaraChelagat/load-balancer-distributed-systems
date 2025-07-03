
# server/app.py
from flask import Flask, jsonify
import os

app = Flask(__name__)

# Get the server ID from the environment variable
SERVER_ID = os.getenv("SERVER_ID", "unknown")

#TASK1
#1.Endpoint(/home, method=GET)
@app.route("/home", defaults={"path": ""})
@app.route("/home/<path:path>")
def home(path):
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "path": path,
        "status": "successful"
    }), 200

#2.Endpoint(/heartbeat, method=GET)
@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
