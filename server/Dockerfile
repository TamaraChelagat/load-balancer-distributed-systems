# server/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy code and requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

# Expose port 5000
EXPOSE 5000

# Define default environment variable
ENV SERVER_ID=0

# Run the server
CMD ["python", "app.py"]
