from flask import Flask, jsonify, request
import random
import string
import requests
import logging
import time
from consistent_hash import ConsistentHashRing

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NUM_SERVERS = 3
VIRTUAL_NODES = 9
SLOTS = 512
SERVER_PORT = 5000

# Initialize with actual server names
server_names = [f"Server{i+1}" for i in range(NUM_SERVERS)]
hash_ring = ConsistentHashRing(
    server_names=server_names,
    virtual_nodes=VIRTUAL_NODES,
    slots=SLOTS
)

def generate_random_hostname():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route("/rep", methods=["GET"])
def get_replicas():
    """Endpoint to get current replica status"""
    return jsonify({
        "N": len(server_names),
        "replicas": server_names
    }), 200

@app.route("/add", methods=["POST"])
def add_replicas():
    """Add new server replicas"""
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({"error": "Too many hostnames provided"}), 400

    new_servers = []
    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else generate_random_hostname()
        if name not in server_names:
            server_names.append(name)
            hash_ring.add_server(name)  # Use the add_server method
            new_servers.append(name)

    return jsonify({
        "message": {
            "N": len(server_names),
            "replicas": server_names
        },
        "status": "successful"
    }), 200

@app.route("/rm", methods=["DELETE"])
def remove_replicas():
    """Remove server replicas"""
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({"error": "Too many hostnames provided"}), 400

    to_remove = []
    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else random.choice(server_names)
        if name in server_names:
            server_names.remove(name)
            hash_ring.remove_server(name)  # Use the remove_server method
            to_remove.append(name)

    return jsonify({
        "message": {
            "N": len(server_names),
            "replicas": server_names
        },
        "status": "successful"
    }), 200

@app.route("/<path:req_path>", methods=["GET"])
def route_request(req_path):
    """Route request to appropriate server"""
    try:
        # Generate unique request key
        request_key = f"{req_path}-{time.time()}"
        
        # Get target server directly by name
        target_server = hash_ring.get_server(request_key)
        if not target_server:
            return jsonify({"error": "No servers available"}), 500
        
        logger.info(f"Routing request to {target_server}")
        
        # Forward request to target server
        response = requests.get(
            f"http://{target_server}:{SERVER_PORT}/{req_path}",
            timeout=3
        )
        return response.json(), response.status_code
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {target_server} failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Routing error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    # Visualize the initial hash ring distribution
    hash_ring.visualize()
    app.run(host="0.0.0.0", port=5000)  # Changed to 5001 to match your setup
