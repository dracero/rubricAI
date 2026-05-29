#!/bin/bash
set -e

# 1. Generación dinámica de config.php si no existe (Persistencia en volumen)
if [ ! -f "/var/www/html/config.php" ]; then
    cat <<EOF > "/var/www/html/config.php"
<?php
unset(\$CFG);
global \$CFG;
\$CFG = new stdClass();

// Variables de entorno de Base de Datos
\$CFG->dbtype    = getenv('DB_TYPE') ?: 'pgsql';
\$CFG->dblibrary = 'native';
\$CFG->dbhost    = getenv('DB_HOST') ?: 'db';
\$CFG->dbname    = getenv('DB_NAME') ?: 'moodle';
\$CFG->dbuser    = getenv('DB_USER') ?: 'moodleuser';
\$CFG->dbpass    = getenv('DB_PASS') ?: 'password';
\$CFG->prefix    = 'mdl_';
\$CFG->dboptions = array('dbpersist' => 0, 'dbport' => getenv('DB_PORT') ?: 5432, 'dbsocket' => '');

// Variables de entorno de Moodle
\$CFG->wwwroot   = getenv('MOODLE_URL') ?: 'http://localhost:8080';
\$CFG->dataroot  = getenv('MOODLE_DATA_ROOT') ?: '/var/www/moodledata';
\$CFG->admin     = 'admin';
\$CFG->directorypermissions = 0777;
\$CFG->slasharguments = true;

// Fix para puerto 8080 local y SSL en Proxy
if (strpos(\$CFG->wwwroot, ':8080') !== false) {
    \$_SERVER['SERVER_PORT'] = 8080;
}
if (isset(\$_SERVER['HTTP_X_FORWARDED_PROTO']) && \$_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
    \$CFG->sslproxy = true;
}

require_once(__DIR__ . '/lib/setup.php');
EOF
    chmod 644 "/var/www/html/config.php"
    echo "config.php generado con éxito."
fi

# 2. Asegurar carpeta de desarrollo local
mkdir -p "/var/www/html/local/rubricai"

# 3. Ajuste de permisos para www-data (Solo sobre lo necesario)
echo "Ajustando permisos internos..."
chown -R www-data:www-data "/var/www/html/local/rubricai" || true
chown www-data:www-data "/var/www/html/config.php" || true

# 4. Pasar ejecución al comando original (php-fpm)
exec "$@"
