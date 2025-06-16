from flask import Flask, jsonify, request
import subprocess #run docker commands
import random #unique container names
import string
from consistent_hash import ConsistentHashRing

app = Flask(__name__)

# Global configuration
NUM_SERVERS = 3
VIRTUAL_NODES = 9
SLOTS = 512

# Track running server container names
server_names = [f"Server{i+1}" for i in range(NUM_SERVERS)]


hash_ring = ConsistentHashRing(num_servers=NUM_SERVERS, virtual_nodes_per_server=VIRTUAL_NODES, slots=SLOTS)


def generate_random_hostname():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

#Starts a server container with the name server_name on Docker network n1
def start_server_container(server_name):
    subprocess.run(["docker", "run", "-d", "--name", server_name, "-e", f"SERVER_ID={server_name}",
                    "--network", "n1", "simple-server"], stdout=subprocess.DEVNULL)

#Stops and removes the specified server container
def stop_and_remove_container(server_name):
    subprocess.run(["docker", "rm", "-f", server_name], stdout=subprocess.DEVNULL)

#replica status
@app.route("/rep", methods=["GET"])
def get_replicas():
    return jsonify({
        "N": len(server_names),
        "replicas": server_names
    }), 200

#Addign new server instances to scale up with increasing client numbers
@app.route("/add", methods=["POST"])
def add_replicas():
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({"error": "Too many hostnames provided."}), 400

#For each new server: use a given hostname if available; otherwise, it generates one
    new_servers = []

    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else generate_random_hostname()
        if name in server_names:
            continue  # avoid duplicates
        server_names.append(name)
        start_server_container(name)
        new_servers.append(name)

    return jsonify({
        "message": {
            "N": len(server_names),
            "replicas": server_names
        },
        "status": "successful"
    }), 200


#Removes server instances to scale down with decresing client or system maintenance  
@app.route("/rm", methods=["DELETE"])
def remove_replicas():
    data = request.get_json()
    n = data.get("n", 0)
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({"error": "Too many hostnames in payload."}), 400

    to_remove = []
#Removes up to n containers either specified or randomly selected
    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else random.choice(server_names)
        if name in server_names:
            server_names.remove(name)
            stop_and_remove_container(name)
            to_remove.append(name)

    return jsonify({
        "message": {
            "N": len(server_names),
            "replicas": server_names
        },
        "status": "successful"
    }), 200

#Request in this endpoint gets routed to a server replica as scheduled by the consistenthashing algorithm of the load balancer
@app.route("/<path:req_path>", methods=["GET"])
def route_request(req_path):
    # Use the path string itself as a hash input
    request_id = sum(ord(c) for c in req_path) % SLOTS
    target_server = hash_ring.get_server_for_request(request_id)

    if target_server is None:
        return jsonify({"error": "No server found"}), 500

    try:
        server_name = server_names[target_server]
    except IndexError:
        return jsonify({"error": "Target server index out of range"}), 500

    try:
        result = subprocess.run(
            ["docker", "exec", server_name, "curl", "-s", f"http://localhost:5000/{req_path}"],
            capture_output=True, text=True
        )
        return result.stdout, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
