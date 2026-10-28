#!/usr/bin/env bash
# Commit local changes under claude-config/, pull others' changes, push.
# Never force-pushes. On conflict it stops and logs; resolve by hand.
set -uo pipefail

REPO_DIR="${GAMA1_REPO_DIR:-$HOME/src/GAMA-1}"
LOG="${XDG_STATE_HOME:-$HOME/.local/state}/claude-sync.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "--- $(date -Is) $(hostname)"

cd "$REPO_DIR" || { echo "repo not found: $REPO_DIR"; exit 1; }

exec 9>"$REPO_DIR/.git/claude-sync.lock"
flock -n 9 || { echo "another sync is running"; exit 0; }

if [ -n "$(git status --porcelain -- claude-config)" ]; then
  git add -- claude-config
  git commit -q -m "claude-config: sync from $(hostname)" -- claude-config
  echo "committed local changes"
fi

if ! git pull -q --rebase --autostash; then
  git rebase --abort 2>/dev/null
  echo "PULL CONFLICT: resolve manually in $REPO_DIR"
  exit 1
fi

if [ -n "$(git log -1 --format=%H @{u}..HEAD 2>/dev/null)" ]; then
  git push -q && echo "pushed" || echo "PUSH FAILED"
fi
echo "ok"
