FROM python:3.11.9-slim

WORKDIR /app

# Instalar dependencias del sistema y limpiar cache de apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar el cache de capas
COPY requirements.txt .

# Usar BuildKit cache mount para acelerar la instalación de pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

EXPOSE 8000

# Comando de inicio (ajustado para desarrollo/producción)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
