FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema (incluye Chromium que usa nodriver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 10000

# Importante: 1 solo worker para no multiplicar el consumo de RAM
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "180", "--workers", "1", "--threads", "2", "app:app"]
