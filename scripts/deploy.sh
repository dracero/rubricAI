#!/bin/bash
set -e

echo "--- Iniciando Despliegue de RubricAI ---"

# 1. Obtener los últimos cambios de Git
echo "Pulling latest changes from Git..."
git pull origin main

# 2. Reconstruir y levantar los contenedores
echo "Building and restarting containers..."
docker compose up -d --build

# 3. Limpieza de caché de Moodle 
echo "Purging Moodle cache..."
docker compose exec moodle php admin/cli/purge_caches.php

# 4. Estado de los contenedores
docker compose ps
echo "--- Despliegue Completado en rubricai.site ---"
