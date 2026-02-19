# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Generate gRPC Python files from proto
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. generate.proto

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import grpc; grpc.aio.aio.insecure_channel('localhost:50051')" || exit 1

# Run gRPC server
CMD ["python", "grpc_server.py"]
