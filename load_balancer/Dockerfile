FROM python:3.12-slim

WORKDIR /app

# Copy requirements.txt from the build context (top-level) into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code into the container
COPY . .

CMD ["python", "balancer.py"]
