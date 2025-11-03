#!/usr/bin/env bash
set -euo pipefail

# --- конфигурация через окружение ---
# POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
# S3_BUCKET (необязательно), S3_PATH (необязательно), RETENTION_DAYS (необязательно)

DATE=$(date +"%Y-%m-%d_%H-%M-%S")
TMP_DIR="/backups/tmp"
FINAL_DIR="/backups"
LOCK_DIR="/var/lock/backup.lock"
ERR_FILE="$FINAL_DIR/backup_${DATE}.err"
DUMP_BASE="backup_${DATE}.sql"
DUMP_FILE="$TMP_DIR/$DUMP_BASE"
GZ_FILE="$FINAL_DIR/${DUMP_BASE}.gz"

mkdir -p "$TMP_DIR" "$FINAL_DIR" || true

# --- вывод окружения для отладки ---
echo "[$(date)] Backup starting with environment:"
echo "  POSTGRES_HOST     = ${POSTGRES_HOST:-localhost}"
echo "  POSTGRES_USER     = ${POSTGRES_USER:-postgres}"
echo "  POSTGRES_DB       = ${POSTGRES_DB:-postgres}"
echo "  POSTGRES_PASSWORD = ${POSTGRES_PASSWORD:+******}"   # скрываем сам пароль
echo "  S3_BUCKET         = ${S3_BUCKET:-<not set>}"
echo "  S3_PATH           = ${S3_PATH:-<not set>}"
echo "  RETENTION_DAYS    = ${RETENTION_DAYS:-<not set>}"
echo "  OUTPUT_DIR        = $FINAL_DIR"

# простая блокировка на запуск (mkdir атомарен)
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date)] Another backup is running — exit."
  exit 0
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

# экспорт пароля для non-interactive pg_dump (альтернативы: .pgpass)
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

echo "[$(date)] Starting pg_dump -> $DUMP_FILE"

# Выполняем pg_dump в plain файл (не в stdout/pipe) и сохраняем stderr в ERR_FILE
pg_dump \
  -h "${POSTGRES_HOST:-localhost}" \
  -U "${POSTGRES_USER:-postgres}" \
  -d "${POSTGRES_DB:-postgres}" \
  --no-owner --format=plain \
  --encoding=UTF8 \
  --file="$DUMP_FILE" \
  2> "$ERR_FILE" || {
    echo "[$(date)] pg_dump failed. See $ERR_FILE"
    cat "$ERR_FILE"
    exit 1
  }


# проверка размера дампа
DUMP_SIZE=$(wc -c < "$DUMP_FILE" 2>/dev/null || echo 0)
if [ "$DUMP_SIZE" -le 0 ]; then
  echo "[$(date)] Dump file is empty ($DUMP_SIZE bytes). Check $ERR_FILE"
  cat "$ERR_FILE"
  exit 1
fi

echo "[$(date)] Dump created, size: ${DUMP_SIZE} bytes. Compressing..."

# компрессия
gzip -c "$DUMP_FILE" > "$GZ_FILE"
GZ_SIZE=$(wc -c < "$GZ_FILE" 2>/dev/null || echo 0)
echo "[$(date)] Compressed to $GZ_FILE (${GZ_SIZE} bytes)"

# опциональная загрузка в S3
if [ -n "${S3_BUCKET:-}" ]; then
  S3_DEST="s3://$S3_BUCKET/${S3_PATH:-}"
  echo "[$(date)] Uploading to $S3_DEST"
  aws s3 cp "$GZ_FILE" "$S3_DEST" || {
    echo "[$(date)] Upload failed"
    exit 1
  }
  echo "[$(date)] Upload succeeded"
fi

# очистка временного файла
rm -f "$DUMP_FILE"

# ротация
if [ -n "${RETENTION_DAYS:-}" ] && [ "${RETENTION_DAYS}" -gt 0 ]; then
  echo "[$(date)] Removing backups older than ${RETENTION_DAYS} days"
  find "$FINAL_DIR" -maxdepth 1 -type f -name "backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete || true
fi

echo "[$(date)] Backup finished successfully: $GZ_FILE"
