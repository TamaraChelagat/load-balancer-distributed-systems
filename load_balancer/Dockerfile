FROM python:3.12-slim

WORKDIR /app

# Install curl and system dependencies needed by pip
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code into the container
COPY . .

# Expose port (optional, useful for documentation or direct run)
EXPOSE 5000

# Run the balancer
CMD ["python", "balancer.py"]
