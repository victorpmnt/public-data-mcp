#!/bin/sh
set -eu

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -v extractor_password="$EXTRACTOR_DB_PASSWORD" \
  -v mcp_password="$MCP_DB_PASSWORD" \
  -v db_name="$POSTGRES_DB" \
  -v admin_user="$POSTGRES_USER" \
  -f /docker-init-db.sql
