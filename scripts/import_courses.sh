#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SRC="$SCRIPT_DIR/../Cursos - Copias de seguridad-20260523T223114Z-3-001/Cursos - Copias de seguridad"

echo "=== Paso 1: Creando carpeta de backups dentro del contenedor Moodle ==="
docker compose exec moodle mkdir -p /var/www/moodledata/backups

echo "=== Paso 2: Copiando archivos de copia de seguridad al contenedor ==="
docker cp "$BACKUP_SRC/." moodle_app:/var/www/moodledata/backups/

echo "=== Paso 3: Descomprimiendo archivo zip dentro del contenedor ==="
docker compose exec moodle unzip -o /var/www/moodledata/backups/wetransfer_entre_cables-mbz_2026-05-21_1821.zip -d /var/www/moodledata/backups/

echo "=== Paso 4: Ajustando permisos de los archivos para Moodle ==="
docker compose exec moodle chown -R www-data:www-data /var/www/moodledata/backups

echo "=== Paso 5: Restaurando cursos en Moodle ==="
mbz_files=$(docker compose exec -u www-data moodle find /var/www/moodledata/backups/ -name "*.mbz")

for file in $mbz_files; do
    # Eliminar posibles saltos de línea adicionales (\r)
    file=$(echo "$file" | tr -d '\r')
    if [ -z "$file" ]; then continue; fi
    echo "--------------------------------------------------------"
    echo "Iniciando restauración de: $(basename "$file")"
    docker compose exec -u www-data moodle php admin/cli/restore_backup.php --file="$file" --categoryid=1
    echo "Finalizado: $(basename "$file")"
done

echo "=== ¡Todos los cursos han sido restaurados con éxito! ==="
