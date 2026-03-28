#!/bin/bash
set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-telemedicina}"
DB_USER="${POSTGRES_USER:-telemedicina}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup..."

docker exec postgres pg_dump -U "$DB_USER" -F c -b -f /tmp/backups/"${DB_NAME}_${TIMESTAMP}.sqlc" "$DB_NAME"

docker cp "postgres:/tmp/backups/${DB_NAME}_${TIMESTAMP}.sqlc" "$BACKUP_DIR/"

docker exec postgres rm /tmp/backups/"${DB_NAME}_${TIMESTAMP}.sqlc"

echo "Backup completed: ${DB_NAME}_${TIMESTAMP}.sqlc"

find "$BACKUP_DIR" -name "*.sqlc" -mtime +"$RETENTION_DAYS" -delete

echo "Old backups cleaned up (retention: $RETENTION_DAYS days)"
