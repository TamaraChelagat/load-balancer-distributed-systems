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

    async def run_experiment(self, num_servers, num_requests=10000):
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
        """Test server failure and recovery"""
        print("\n=== Testing Failure Recovery ===")

        servers = await self.get_current_servers()
        print(f"Initial servers: {servers}")

        if not servers:
            print("No servers available for failure test.")
            return

        failed_server = servers[0]
        print(f"\nSimulating failure of {failed_server}")

        # In real use, you'd actually kill the container. Here we just run requests.
        server_hits = Counter()
        for i in range(1000):
            server_id = await self.make_request(f"failtest-{i}")
            if server_id:
                server_hits[server_id] += 1

        print("\nRequest distribution during simulated failure:")
        for server, count in server_hits.items():
            print(f"{server}: {count} requests")

        new_servers = await self.get_current_servers()
        print(f"\nCurrent servers: {new_servers}")

        if len(new_servers) == len(servers):
            print("\nWarning: Server count didn't change - check your failure detection logic!")
        else:
            print("\nLoad balancer successfully maintained server count.")

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
