#!/bin/sh
set -e
STORAGE_ROOT="${STORAGE_ROOT:-/data/storage}"
if [ "$(id -u)" = "0" ]; then
  mkdir -p "$STORAGE_ROOT"
  chown -R appuser:appuser "$STORAGE_ROOT"
  exec /usr/sbin/runuser -u appuser -- "$@"
fi
exec "$@"
