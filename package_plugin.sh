#!/bin/bash

# Script para empaquetar el plugin RubricAI para Moodle
# Este script genera un archivo .zip que puede subirse a otro Moodle
# a través de la interfaz de "Instalar plugins".

PLUGIN_DIR="local/rubricai"
OUTPUT_ZIP="rubricai_plugin.zip"

if [ ! -d "$PLUGIN_DIR" ]; then
    echo "Error: No se encontró el directorio del plugin en $PLUGIN_DIR"
    exit 1
fi

echo "🚀 Iniciando empaquetado de RubricAI..."

# Crear un directorio temporal para construir la estructura
TMP_DIR=$(mktemp -d)
mkdir -p "$TMP_DIR/rubricai"

# Copiar los archivos del plugin al directorio temporal
cp -r "$PLUGIN_DIR/"* "$TMP_DIR/rubricai/"

# Limpieza: Eliminar archivos locales o temporales que no deben ir en el zip
rm -f "$TMP_DIR/rubricai/rubricai.ini"

# Crear un archivo de ejemplo para la configuración
cat <<EOF > "$TMP_DIR/rubricai/rubricai.ini.example"
; Archivo de configuración para el plugin RubricAI
; Renombra este archivo a rubricai.ini en tu servidor Moodle
; y define la URL de tu servicio de IA.
rubricai_ai_url = "https://tu-dominio-ia.com"
EOF

# Entrar al directorio temporal y comprimir
# Moodle espera que el ZIP contenga una carpeta con el nombre del plugin
cd "$TMP_DIR"
zip -r "rubricai.zip" rubricai/ > /dev/null

# Mover el resultado a la raíz del proyecto
cd - > /dev/null
mv "$TMP_DIR/rubricai.zip" "$OUTPUT_ZIP"

# Limpiar directorio temporal
rm -rf "$TMP_DIR"

echo "✅ Éxito: Plugin empaquetado en $OUTPUT_ZIP"
echo "Ya puedes subir este archivo a otro Moodle en: Administración del sitio > Plugins > Instalar plugins."
