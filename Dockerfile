FROM python:3.13-slim

# System deps: libmagic (python-magic), ffmpeg, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmagic1 \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data dirs
RUN mkdir -p auth data/chats data/webhooks logs tmp

EXPOSE 8300

ENV PORT=8300 \
    ENABLE_FFMPEG_WARMUP=1 \
    ENABLE_WHATSAPP=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8300/status || exit 1

CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", "--port", "8300", \
     "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--log-level", "info"]
