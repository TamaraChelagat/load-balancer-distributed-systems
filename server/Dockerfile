# server/Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

#Install curl
RUN apt-get update && apt-get install -y curl
# Copy code and requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

# Expose port 5000
EXPOSE 5000

# Define default environment variable
ENV SERVER_ID=0

# Run the server
CMD ["python", "app.py"]
