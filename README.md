
# **Load Balancer Assignment**  
**Distributed Systems Course**  

### **Overview**  
A dynamic load balancer that distributes incoming requests across multiple backend servers, with analysis scripts to evaluate performance under different configurations (e.g., round-robin, least connections).  

**Key Features**:  
- Adjustable server pool (add/remove replicas dynamically).  
- Multiple routing algorithms (e.g., Round Robin, Least Connections).  
- Simulation and analysis tools (e.g., `analysis_task4.py`).  
- Metrics: Throughput, latency, error rates.  

---

### **Repository Structure**  
```
.
├── src/                     # Load balancer implementation
│   ├── load_balancer.py     # Core logic
│   ├── server.py            # Backend server mock
├── analysis/                # Performance tests
│   ├── analysis_task4.py    # Experiment runner (e.g., N=3 servers)
│   ├── plots/               # Generated graphs
├── docs/                    # Design documents
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

### **Requirements**  
- Python 3.10+  
- Libraries: `asyncio`, `aiohttp`, `matplotlib`, `numpy`  
- (Optional) Docker for containerized servers.  

Install dependencies:  
```bash
pip install -r requirements.txt
```

---

### **How to Run**  
1. **Start Backend Servers**:  
   ```bash
   python src/server.py --port 5000  # Repeat for 5001, 5002...
   ```
2. **Launch Load Balancer**:  
   ```bash
   python src/load_balancer.py --algorithm round_robin
   ```
3. **Run Analysis**:  
   ```bash
   python analysis/analysis_task4.py
   ```

---

### **Analysis Tasks**  
| Task      | Description                          | Command               |
|-----------|--------------------------------------|-----------------------|
| **A-1**   | Fixed server count (N=3)             | `python analysis_task4.py --scenario A1` |
| **A-2**   | Variable server count (N=1..5)       | `python analysis_task4.py --scenario A2` |
| **B**     | Compare routing algorithms           | `python analysis_task4.py --compare` |

**Expected Output**:  
- CSV files with metrics (`results.csv`).  
- Plots in `analysis/plots/`.  

---

### **Debugging**  
If you encounter `KeyError: 'message'` (like in `analysis_task4.py`):  
1. Check the API response format:  
   ```python
   print("Raw response:", response.json())  # Add this before parsing
   ```
2. Validate the server is running:  
   ```bash
   curl http://localhost:5001/rep
   ```
3. Update the parsing logic if the response lacks `message.replicas`.  

---


**License**  
[MIT](LICENSE)  

---


