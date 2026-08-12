#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_ROOT="$(realpath "$REPO_ROOT/src/results/closeout_dsr")"
SOURCE_PATH="${1:-}"

if [[ -z "$SOURCE_PATH" || ! -d "$SOURCE_PATH" ]]; then
  printf 'Usage: %s PATH_TO_FAILED_CLOSEOUT_RUN\n' "$0" >&2
  exit 2
fi

SOURCE_PATH="$(realpath "$SOURCE_PATH")"
if [[ "$(dirname "$SOURCE_PATH")" != "$RESULTS_ROOT" ]]; then
  printf 'Only an immediate child of the closeout results directory may be archived: %s\n' "$SOURCE_PATH" >&2
  exit 2
fi
if [[ "$(basename "$SOURCE_PATH")" == "failed_attempts" ]]; then
  printf 'The archive directory itself cannot be archived.\n' >&2
  exit 2
fi
if ! grep -qx 'status=failed' "$SOURCE_PATH/run_status.txt" 2>/dev/null; then
  printf 'Refusing to move a run that is not explicitly marked failed: %s\n' "$SOURCE_PATH" >&2
  exit 2
fi
if [[ -f "$SOURCE_PATH/launcher.pid" ]]; then
  launcher_pid="$(<"$SOURCE_PATH/launcher.pid")"
  if [[ "$launcher_pid" =~ ^[0-9]+$ ]] && kill -0 "$launcher_pid" 2>/dev/null; then
    printf 'Launcher PID %s is still running; refusing to archive.\n' "$launcher_pid" >&2
    exit 2
  fi
fi

ARCHIVE_ROOT="$RESULTS_ROOT/failed_attempts"
mkdir -p "$ARCHIVE_ROOT"
TARGET_PATH="$ARCHIVE_ROOT/$(basename "$SOURCE_PATH")_$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -e "$TARGET_PATH" ]]; then
  printf 'Archive target already exists: %s\n' "$TARGET_PATH" >&2
  exit 2
fi

mv -- "$SOURCE_PATH" "$TARGET_PATH"
printf 'Failed attempt preserved at: %s\n' "$TARGET_PATH"
printf 'The exact frozen matrix may now be relaunched after the infrastructure cause is fixed.\n'
