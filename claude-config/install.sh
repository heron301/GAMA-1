#!/usr/bin/env bash
# Link this machine's ~/.claude to the shared config in heron301/GAMA-1.
# Works on Linux, WSL2, and Omarchy (Arch). Safe to run more than once.
set -euo pipefail

REPO_URL="${GAMA1_REPO_URL:-git@github.com:heron301/GAMA-1.git}"
REPO_DIR="${GAMA1_REPO_DIR:-$HOME/src/GAMA-1}"
CLAUDE_DIR="$HOME/.claude"
SHARED="$REPO_DIR/claude-config/home"
ITEMS=(CLAUDE.md settings.json agents commands skills)

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Cloning $REPO_URL -> $REPO_DIR"
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone "$REPO_URL" "$REPO_DIR"
fi

mkdir -p "$CLAUDE_DIR"
backup="$CLAUDE_DIR/backup-$(date +%Y%m%d-%H%M%S)"

for item in "${ITEMS[@]}"; do
  target="$CLAUDE_DIR/$item"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$SHARED/$item" ]; then
    echo "ok      $target"
    continue
  fi
  if [ -e "$target" ] || [ -L "$target" ]; then
    mkdir -p "$backup"
    mv "$target" "$backup/"
    echo "backup  $target -> $backup/$item"
  fi
  ln -s "$SHARED/$item" "$target"
  echo "linked  $target -> $SHARED/$item"
done

ln -sfn "$REPO_DIR/claude-config/sync.sh" "$CLAUDE_DIR/claude-sync.sh"
echo "linked  $CLAUDE_DIR/claude-sync.sh"

# Hourly sync, in addition to the SessionStart hook in settings.json.
if systemctl --user show-environment >/dev/null 2>&1; then
  unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  cat > "$unit_dir/claude-sync.service" <<UNIT
[Unit]
Description=Sync shared Claude config with GitHub

[Service]
Type=oneshot
ExecStart=/usr/bin/env bash $CLAUDE_DIR/claude-sync.sh
UNIT
  cat > "$unit_dir/claude-sync.timer" <<UNIT
[Unit]
Description=Hourly Claude config sync

[Timer]
OnBootSec=2min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
UNIT
  systemctl --user daemon-reload
  systemctl --user enable --now claude-sync.timer
  echo "timer   systemd user timer enabled (claude-sync.timer)"
else
  echo "timer   systemd user session not available; relying on the SessionStart hook."
  echo "        On WSL2, enable systemd in /etc/wsl.conf ([boot] systemd=true) and rerun."
fi

if [ -d "$backup" ]; then
  echo
  echo "Review $backup. Move anything you want shared into $SHARED and run claude-sync.sh."
fi
echo "Done."
