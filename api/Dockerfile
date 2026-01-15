FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# libgl1, libglib2.0-0: for OpenCV
# build-essential: for compiling C++ extensions
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create package structure
RUN mkdir -p /app/api
COPY . /app/api/

# Install the C++ extension
# We switch to /app/api to run setup.py
WORKDIR /app/api
RUN pip install .

# Switch back to /app for running the app
WORKDIR /app

# Add /app to PYTHONPATH so "import api" works
ENV PYTHONPATH=/app

# Run from /app to allow "api.main" module resolution
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
