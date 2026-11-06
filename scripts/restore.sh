#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <backup-file> [--yes]" >&2
  exit 1
fi

FILE="$(realpath "$1")"
if [[ ! -f "$FILE" ]]; then
  echo "error: backup file not found: $FILE" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "error: .env not found in $ROOT_DIR" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
TARGET_DB="${TARGET_DB:-$POSTGRES_DB}"

if [[ "${2:-}" != "--yes" ]]; then
  read -r -p "This will overwrite data in '$TARGET_DB'. Continue? [y/N] " answer
  if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
    echo "Aborted."
    exit 1
  fi
fi

docker compose exec -T postgres pg_restore \
  --username "$POSTGRES_USER" \
  --dbname "$TARGET_DB" \
  --clean \
  --if-exists \
  --no-owner \
  < "$FILE"

echo "Restore into '$TARGET_DB' complete."
