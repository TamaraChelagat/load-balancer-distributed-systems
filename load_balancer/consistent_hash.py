import math
import matplotlib.pyplot as plt
from collections import Counter


class ConsistentHashRing:
    def __init__(self, num_servers=3, virtual_nodes_per_server=9, slots=512):
        self.num_servers = num_servers
        self.virtual_nodes = virtual_nodes_per_server
        self.slots = slots
        self.ring = [None] * slots  # each slot points to a server_id
        self.server_map = {}  # maps server_id -> list of slots

        self._initialize_ring()

    def _hash_virtual(self, server_id, replica_id):
        # Φ(i, j) = i + j + 2^j + 25 mod 512
        return (server_id + replica_id + 2 ** replica_id + 25) % self.slots # consistent hash for virtual nodes

    def _hash_request(self, request_id):
        # H(i) = i + 2^i + 17 mod 512
        return (request_id + 2 ** request_id + 17) % self.slots

    def _linear_probe(self, start):
        for i in range(self.slots): #iterates to find a free slot
            idx = (start + i) % self.slots
            if self.ring[idx] is None: #avoids collisions btwn virtual servers
                return idx
        raise Exception("Hash ring is full") 

    def _initialize_ring(self):
        for server_id in range(self.num_servers):
            self.server_map[server_id] = []
            for replica in range(self.virtual_nodes):
                slot = self._hash_virtual(server_id, replica)
                if self.ring[slot] is not None:
                    slot = self._linear_probe(slot)
                self.ring[slot] = server_id
                self.server_map[server_id].append(slot)

    def get_server_for_request(self, request_id):
        slot = self._hash_request(request_id)
        for i in range(self.slots):
            idx = (slot + i) % self.slots
            if self.ring[idx] is not None:
                return self.ring[idx]
        return None

# #TESTING THE CONSISTENT HASH RING 

# if __name__ == "__main__":
#     ch = ConsistentHashRing()

#     print("=== Request Routing ===")
#     for req in range(10):
#         server = ch.get_server_for_request(req)
#         print(f"Request {req} routed to Server {server}")

#     print("\n=== Slot Assignments ===")
#     for i, server_id in enumerate(ch.ring):
#         if server_id is not None:
#             print(f"Slot {i} -> Server {server_id}")
     
    
# server_counts = Counter(ch.ring)
# if None in server_counts:
#     del server_counts[None]

# # Prepare labels and data
# labels = [f"Server {sid}" for sid in server_counts.keys()]
# sizes = list(server_counts.values())


# # --- PIE CHART ---
# plt.figure(figsize=(6,6))
# plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
# plt.title("Slot Ownership per Server (Consistent Hashing)")
# plt.axis('equal')  # Equal aspect ratio ensures pie is round.
# plt.show()
    
