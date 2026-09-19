#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_PASSWORD:?BACKUP_PASSWORD is required}"

output="${1:-filet-pattern-backup-$(date -u +%Y%m%dT%H%M%SZ).sql.gz.enc}"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT HUP INT TERM

pg_dump --dbname="$DATABASE_URL" --no-owner --no-privileges \
  | gzip -9 \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
      -pass env:BACKUP_PASSWORD -out "$temporary/backup.enc"
mv "$temporary/backup.enc" "$output"
echo "Encrypted backup created: $output"
