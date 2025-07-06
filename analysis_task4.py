import asyncio
import aiohttp
import matplotlib.pyplot as plt
import random
import time
from collections import Counter
import numpy as np

class LoadBalancerAnalyzer:
    def __init__(self, balancer_url="http://localhost:5001"):
        self.balancer_url = balancer_url
        self.session = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def make_request(self, request_id):
        """Make a single request to the load balancer"""
        try:
            url = f"{self.balancer_url}/home?req={request_id}-{time.time()}"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    msg = data.get("message", "")
                    if "Server:" in msg:
                        return msg.split("Server:")[1].strip()
        except Exception as e:
            print(f"Request failed: {e}")
        return None

    async def run_experiment(self, num_servers, num_requests=1000):
        """Run a single experiment with given parameters"""
        server_hits = Counter()

        # Ensure desired number of servers
        await self.adjust_server_count(num_servers)

        # Send requests asynchronously
        tasks = [self.make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

        for server_id in results:
            if server_id:
                server_hits[server_id] += 1

        return server_hits

    async def adjust_server_count(self, target_count):
        """Adjust number of servers to target count"""
        current_servers = await self.get_current_servers()
        current_count = len(current_servers)

        if current_count < target_count:
            payload = {"n": target_count - current_count}
            async with self.session.post(
                f"{self.balancer_url}/add",
                json=payload
            ) as resp:
                await resp.json()
        elif current_count > target_count:
            payload = {"n": current_count - target_count}
            async with self.session.delete(
                f"{self.balancer_url}/rm",
                json=payload
            ) as resp:
                await resp.json()

    async def get_current_servers(self):
        """Safely retrieve the list of replicas"""
        try:
            async with self.session.get(f"{self.balancer_url}/rep") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "replicas" in data:
                        return data["replicas"]
                    else:
                        print(f"Unexpected /rep response format: {data}")
                        return []
                else:
                    print(f"Error fetching /rep: HTTP {resp.status}")
                    return []
        except Exception as e:
            print(f"Failed to query /rep: {e}")
            return []

    def plot_request_distribution(self, server_hits, title):
        """Plot request distribution as bar chart"""
        servers = sorted(server_hits.keys())
        counts = [server_hits[s] for s in servers]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(servers, counts, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])

        plt.title(title)
        plt.xlabel("Server ID")
        plt.ylabel("Number of Requests")

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig("request_distribution.png")
        plt.show()

    def plot_scalability(self, results):
        """Plot scalability results as line chart"""
        plt.figure(figsize=(10, 6))

        for num_servers, server_hits in results.items():
            avg_load = sum(server_hits.values()) / num_servers
            std_dev = np.std(list(server_hits.values()))

            plt.errorbar(
                num_servers, avg_load, yerr=std_dev,
                fmt='-o', label=f'N={num_servers}',
                capsize=5
            )

        plt.title("Average Server Load vs Number of Servers")
        plt.xlabel("Number of Servers")
        plt.ylabel("Average Requests per Server")
        plt.xticks(list(results.keys()))
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig("scalability_analysis.png")
        plt.show()

    async def test_failure_recovery(self):
        """Enhanced server failure and recovery test with explicit removal verification"""
        print("\n=== Testing Failure Recovery ===")
        
        # Scale down to exactly 3 servers first
        print("Ensuring we have exactly 3 servers...")
        await self.adjust_server_count(3)
        await asyncio.sleep(2)  # Allow time for scaling
        
        # Get initial state
        initial_servers = await self.get_current_servers()
        if not initial_servers or len(initial_servers) != 3:
            print(f"ERROR: Expected 3 servers, got {len(initial_servers)}")
            return
            
        print(f"Initial servers: {initial_servers}")
        
        # Take baseline measurements
        print("\nRunning baseline test with 3 servers...")
        baseline_hits = await self.run_experiment(3, 1000)
        print("\nBaseline distribution:")
        for server, count in baseline_hits.items():
            print(f"{server}: {count} requests")

        # Explicitly remove Server1 (or first server if Server1 doesn't exist)
        target_server = "Server1"
        if target_server not in initial_servers:
            target_server = initial_servers[0]
            print(f"Note: Using {target_server} as target since Server1 not found")
            
        print(f"\nActually removing {target_server}...")
        try:
            async with self.session.delete(
                f"{self.balancer_url}/rm",
                json={"n": 1, "specific": target_server}  # Assuming API supports specific removal
            ) as resp:
                if resp.status != 200:
                    print(f"Failed to remove server: HTTP {resp.status}")
                    return
                print(f"Successfully removed {target_server}")
        except Exception as e:
            print(f"Error removing server: {e}")
            return

        # Verify removal
        current_servers = await self.get_current_servers()
        if target_server in current_servers:
            print(f"\nERROR: {target_server} still present after removal")
            return
        print(f"\nCurrent servers after removal: {current_servers}")

        # Re-run test to confirm target handles 0 requests
        print("\nRunning verification test with removed server...")
        verification_hits = await self.run_experiment(2, 1000)
        
        print("\nVerification distribution:")
        for server, count in verification_hits.items():
            print(f"{server}: {count} requests")

        # Check if removed server still getting requests
        if target_server in verification_hits:
            print(f"\nFAILURE: {target_server} still handled {verification_hits[target_server]} requests!")
        else:
            print(f"\nSUCCESS: {target_server} handled 0 requests after removal")

        # Check load distribution
        expected_avg = sum(verification_hits.values()) / 2
        imbalances = [
            abs(count - expected_avg)/expected_avg 
            for count in verification_hits.values()
        ]
        
        if any(imb > 0.25 for imb in imbalances):
            print("\nWARNING: Significant load imbalance after removal")
        else:
            print("\nLoad successfully redistributed to remaining servers")

        # Restore original state
        print("\nRestoring original server count...")
        await self.adjust_server_count(3)

    async def run_all_analyses(self):
        """Run all required analyses"""
        await self.init_session()

        try:
            print("Running Analysis A-1: Fixed server count (N=3)")
            hits_a1 = await self.run_experiment(3)
            self.plot_request_distribution(
                hits_a1,
                "Task 4A-1: Request Distribution (N=3, 10,000 requests)"
            )

            print("\nRunning Analysis A-2: Scalability test")
            scalability_results = {}
            for n in range(2, 7):
                print(f"Testing with {n} servers...")
                hits = await self.run_experiment(n)
                scalability_results[n] = hits
            self.plot_scalability(scalability_results)

            await self.test_failure_recovery()

            print("\nAnalysis A-4: Implement custom hash functions in ConsistentHashRing.")

        finally:
            await self.close_session()

if __name__ == "__main__":
    analyzer = LoadBalancerAnalyzer()
    asyncio.run(analyzer.run_all_analyses())