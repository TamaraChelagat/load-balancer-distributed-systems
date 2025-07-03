FROM python:3.12-slim

WORKDIR /app

# Install curl and docker CLI for subprocess/docker usage
RUN apt-get update \
    && apt-get install -y curl docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy from parent context
COPY ../requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "load_balancer/balancer.py"]
