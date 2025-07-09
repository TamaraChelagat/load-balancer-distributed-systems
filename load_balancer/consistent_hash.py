import bisect
from collections import defaultdict
import matplotlib.pyplot as plt

class ConsistentHashRing:
    def __init__(self, server_names, virtual_nodes=9, slots=512):
        """
        Initialize with actual server names
        :param server_names: List of server names (e.g., ["Server1", "Server2", "Server3"])
        :param virtual_nodes: Number of virtual nodes per server (K)
        :param slots: Total number of slots in the ring (M)
        """
        self.server_names = server_names
        self.virtual_nodes = virtual_nodes
        self.slots = slots
        self.ring = []  # List of (position, server_name)
        
        self._initialize_ring()

    def _request_hash(self, key):
        """Hash function for request mapping: H(i) = i + 2i + 1"""
        i = int(key)
        return (i + 2 * i + 1) % self.slots

    def _virtual_node_hash(self, server_id, vnode_id):
        """Hash function for virtual server mapping: Φ(i,j) = i + j + 2j + 25"""
        i = int(server_id.replace("Server", ""))  # Extract numeric ID
        j = vnode_id
        return (i + j + 2 * j + 25) % self.slots

    def _initialize_ring(self):
        """Initialize the hash ring with virtual nodes"""
        self.ring = []
        for server in self.server_names:
            self._add_server_to_ring(server)

    def _add_server_to_ring(self, server_name):
        """Add a server's virtual nodes to the ring"""
        server_id = server_name.replace("Server", "")
        for j in range(self.virtual_nodes):
            position = self._virtual_node_hash(server_id, j)
            bisect.insort(self.ring, (position, server_name))

    def add_server(self, server_name):
        """Add a new server to the hash ring"""
        if server_name not in self.server_names:
            self.server_names.append(server_name)
            self._add_server_to_ring(server_name)

    def remove_server(self, server_name):
        """Remove a server from the hash ring"""
        if server_name in self.server_names:
            self.server_names.remove(server_name)
            # Remove all virtual nodes for this server
            self.ring = [(pos, srv) for (pos, srv) in self.ring if srv != server_name]

    def get_server(self, key):
        """Get the server responsible for the given key"""
        if not self.ring:
            return None
            
        position = self._request_hash(str(key))
        
        # Find the first node with position >= hash
        idx = bisect.bisect_left(self.ring, (position, ""))
        
        # Wrap around if necessary
        if idx == len(self.ring):
            idx = 0
            
        return self.ring[idx][1]  # Return the server name

    def visualize(self):
        """Visualize the hash ring distribution"""
        plt.figure(figsize=(12, 6))
        
        # Group positions by server
        server_positions = defaultdict(list)
        for pos, server in self.ring:
            server_positions[server].append(pos)
        
        # Create plot
        colors = plt.cm.get_cmap('tab10', len(self.server_names))
        
        for i, server in enumerate(self.server_names):
            positions = server_positions[server]
            plt.scatter(
                positions, [i] * len(positions),
                label=server,
                color=colors(i),
                s=100,
                alpha=0.7
            )
        
        plt.yticks(range(len(self.server_names)), self.server_names)
        plt.title(f"Consistent Hash Ring (Servers: {len(self.server_names)}, Virtual Nodes: {self.virtual_nodes}, Slots: {self.slots})")
        plt.xlabel("Slot Position")
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()


if __name__ == "__main_":
    # Example usage
    ring = ConsistentHashRing(["Server1", "Server2", "Server3"])
    
    print("Hash ring initialized with:")
    print(f"- {len(ring.server_names)} physical servers")
    print(f"- {ring.virtual_nodes} virtual nodes per server")
    print(f"- {ring.slots} total slots")
    
    # Test request routing
    test_keys = [123456, 789012, 345678, 901234]
    for key in test_keys:
        server = ring.get_server(key)
        print(f"Request {key} is routed to {server}")
    
    # Visualize the ring
    ring.visualize()
    
    # Demonstrate adding a server
    print("\nAdding Server4...")
    ring.add_server("Server4")
    ring.visualize()
    
    # Demonstrate removing a server
    print("\nRemoving Server2...")
    ring.remove_server("Server2")
    ring.visualize()
