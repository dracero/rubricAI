#!/bin/bash

# Script para empaquetar el plugin AreteIA para Moodle
# Este script genera un archivo .zip que puede subirse a otro Moodle
# a través de la interfaz de "Instalar plugins".

PLUGIN_DIR="local/areteia"
OUTPUT_ZIP="areteia_plugin.zip"

if [ ! -d "$PLUGIN_DIR" ]; then
    echo "Error: No se encontró el directorio del plugin en $PLUGIN_DIR"
    exit 1
fi

echo "🚀 Iniciando empaquetado de AreteIA..."

# Crear un directorio temporal para construir la estructura
TMP_DIR=$(mktemp -d)
mkdir -p "$TMP_DIR/areteia"

# Copiar los archivos del plugin al directorio temporal
cp -r "$PLUGIN_DIR/"* "$TMP_DIR/areteia/"

# Limpieza: Eliminar archivos locales o temporales que no deben ir en el zip
rm -f "$TMP_DIR/areteia/areteia.ini"

# Crear un archivo de ejemplo para la configuración
cat <<EOF > "$TMP_DIR/areteia/areteia.ini.example"
; Archivo de configuración para el plugin AreteIA
; Renombra este archivo a areteia.ini en tu servidor Moodle
; y define la URL de tu servicio de IA.
areteia_ai_url = "https://tu-dominio-ia.com"
EOF

# Entrar al directorio temporal y comprimir
# Moodle espera que el ZIP contenga una carpeta con el nombre del plugin
cd "$TMP_DIR"
zip -r "areteia.zip" areteia/ > /dev/null

# Mover el resultado a la raíz del proyecto
cd - > /dev/null
mv "$TMP_DIR/areteia.zip" "$OUTPUT_ZIP"

# Limpiar directorio temporal
rm -rf "$TMP_DIR"

echo "✅ Éxito: Plugin empaquetado en $OUTPUT_ZIP"
echo "Ya puedes subir este archivo a otro Moodle en: Administración del sitio > Plugins > Instalar plugins."
