FROM python:3.11-slim

WORKDIR /app

# Install system runtime dependencies for OpenCV, InsightFace, and C++ extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install all python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create necessary directories and configure permissions for Hugging Face Spaces user (UID 1000)
RUN mkdir -p /app/data/faces /app/data/attendance /app/data/training /app/data/unknown_faces /app/models /app/logs \
    && useradd -m -u 1000 user \
    && chown -R user:user /app /home/user \
    && chmod -R 777 /app/data /app/models /app/logs /app

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

EXPOSE 7860

CMD ["python", "app.py"]
