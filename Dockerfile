FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y fuerza salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .

# Render usa el puerto 10000 por defecto
EXPOSE 10000

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "app:app"]
