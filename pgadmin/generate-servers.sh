#!/bin/sh
set -eu

SERVER_JSON_FILE="${PGADMIN_SERVER_JSON_FILE:-/var/lib/pgadmin/servers.json}"

mkdir -p "$(dirname "${SERVER_JSON_FILE}")"

cat > "${SERVER_JSON_FILE}" <<EOF
{
  "Servers": {
    "1": {
      "Name": "${PGADMIN_POSTGRES_SERVER_NAME:-ticketing-system-postgres}",
      "Group": "${PGADMIN_POSTGRES_SERVER_GROUP:-Local}",
      "Host": "${PGADMIN_POSTGRES_HOST:-postgres}",
      "Port": ${PGADMIN_POSTGRES_PORT:-5432},
      "MaintenanceDB": "${POSTGRES_DB:-ticketing_system}",
      "Username": "${POSTGRES_USER:-ticketing_user}",
      "Password": "${POSTGRES_PASSWORD:-ticketing_password}",
      "SSLMode": "${PGADMIN_POSTGRES_SSL_MODE:-prefer}"
    }
  }
}
EOF

chmod 600 "${SERVER_JSON_FILE}"

exec /entrypoint.sh
