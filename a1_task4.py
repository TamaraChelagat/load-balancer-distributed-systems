import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import Counter

BALANCER_URL = "http://localhost:5001"
NUM_REQUESTS = 100

# Store counts per server
server_hits = Counter()

async def fetch(session, key):
    url = f"{BALANCER_URL}/{key}"
    try:
        async with session.get(url) as resp:
            data = await resp.json()
            msg = data.get("message", "")
            for server in ["Server1", "Server2", "Server3"]:
                if server in msg:
                    server_hits[server] += 1
                    
                    break
    except Exception as e:
        print(f"Request failed: {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, f"key{i}") for i in range(NUM_REQUESTS)]
        await asyncio.gather(*tasks)

    # Bar chart
    plt.figure(figsize=(8, 5))
    plt.bar(server_hits.keys(), server_hits.values(), color='skyblue')
    plt.title("Task 4A-1: Request Count per Server (N=3)")
    plt.xlabel("Server")
    plt.ylabel("Number of Requests")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
