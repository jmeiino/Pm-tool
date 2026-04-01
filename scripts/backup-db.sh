#!/bin/bash
# PostgreSQL Backup-Script fuer PM-Tool
# Nutzung: ./scripts/backup-db.sh [backup-verzeichnis]
#
# Erstellt einen pg_dump mit Timestamp und loescht Backups aelter als 7 Tage.

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
CONTAINER="pm-tool-db-1"
DB_USER="pmtool"
DB_NAME="pmtool"
KEEP_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pmtool_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Backup starten: ${DB_NAME} -> ${BACKUP_FILE}"
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup erstellt: ${BACKUP_FILE} (${SIZE})"

# Alte Backups loeschen
DELETED=$(find "$BACKUP_DIR" -name "pmtool_*.sql.gz" -mtime +${KEEP_DAYS} -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "Alte Backups geloescht: ${DELETED} Dateien (aelter als ${KEEP_DAYS} Tage)"
fi

echo "Fertig."
