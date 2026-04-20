#!/bin/sh
set -eu
STORAGE_ROOT="${STORAGE_ROOT:-/data/storage}"

if [ "$(id -u)" = "0" ]; then
  case "$STORAGE_ROOT" in
    ""|/)
      echo "docker-entrypoint: refusing STORAGE_ROOT (empty or /)" >&2
      exit 1
      ;;
    *..*)
      echo "docker-entrypoint: refusing STORAGE_ROOT containing '..': $STORAGE_ROOT" >&2
      exit 1
      ;;
    /data/*) ;;
    *)
      echo "docker-entrypoint: STORAGE_ROOT must be under /data/ (got: $STORAGE_ROOT)" >&2
      exit 1
      ;;
  esac

  mkdir -p "$STORAGE_ROOT"
  appuser_uid=$(id -u appuser)
  dir_uid=$(stat -c '%u' "$STORAGE_ROOT")
  if [ "$dir_uid" != "$appuser_uid" ]; then
    chown -R appuser:appuser "$STORAGE_ROOT"
  fi
  exec /usr/sbin/runuser -u appuser -- "$@"
fi
exec "$@"
