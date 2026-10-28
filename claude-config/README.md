# Shared Claude Config (all machines)

One source of truth for Claude Code on every machine. Each machine links `~/.claude/` items to `claude-config/home/` in this repository. A sync job commits local edits, pulls everyone else's, and pushes.

## What syncs and what does not

| Synced (in git) | Stays local (never in git) |
|---|---|
| `CLAUDE.md` — global instructions | `.credentials.json` — login tokens |
| `settings.json` — permissions, hooks | `projects/`, `history.jsonl` — chat history |
| `agents/` — subagents | `statsig/`, `todos/`, caches |
| `commands/` — slash commands | `settings.local.json` — per-machine overrides |
| `skills/` — skills | MCP server API keys |

Put per-machine settings in `~/.claude/settings.local.json`. Never put secrets in `home/`.

## How sync runs

`sync.sh` commits changes under `claude-config/`, pulls with rebase, and pushes. It never force-pushes. It runs two ways: a `SessionStart` hook in `settings.json` runs it in the background each time Claude Code starts, and a systemd user timer runs it hourly where systemd is available. Log: `~/.local/state/claude-sync.log`. A conflict stops the sync and logs `PULL CONFLICT`; fix it by hand in `~/src/GAMA-1`.

## Prerequisites (every machine)

Git, and GitHub authentication that can push to `heron301/GAMA-1`. Use SSH keys (`ssh -T git@github.com` must succeed) or `gh auth login` plus `GAMA1_REPO_URL=https://github.com/heron301/GAMA-1.git`.

## Setup: XE3 (Windows 11 + WSL2) — primary

1. In WSL, enable systemd so the hourly timer works. Add this to `/etc/wsl.conf`, then run `wsl --shutdown` from PowerShell and reopen WSL:

   ```ini
   [boot]
   systemd=true
   ```

2. In WSL, install and link:

   ```bash
   sudo apt install -y git
   git clone git@github.com:heron301/GAMA-1.git ~/src/GAMA-1
   bash ~/src/GAMA-1/claude-config/install.sh
   ```

3. Review the `~/.claude/backup-*` folder the installer creates. Move any agents, commands, or skills you want shared into `~/src/GAMA-1/claude-config/home/`, then run `~/.claude/claude-sync.sh`.

4. Give WSL Claude access to the Obsidian vault (adjust the Windows path):

   ```bash
   ln -s "/mnt/c/Users/<you>/Documents/<VaultName>" ~/obsidian
   ```

5. Keep the repository on the WSL filesystem (`~/src`), not `/mnt/c`. Git is much faster there and file permissions stay correct.

## Setup: Linux laptop (now) and Omarchy (after reinstall)

```bash
sudo pacman -S --needed git      # Omarchy / Arch  (Ubuntu/Debian: sudo apt install git)
git clone git@github.com:heron301/GAMA-1.git ~/src/GAMA-1
bash ~/src/GAMA-1/claude-config/install.sh
```

When you reinstall the laptop as Omarchy, run the same three lines. Your config comes back in under a minute.

## Setup: any other machine

Run the same three lines. On macOS use `brew install git`. Native Windows Claude Code (outside WSL) is not covered; use WSL.

## Claude Desktop and claude.ai

Claude Desktop (Windows app) and claude.ai do not read `~/.claude/`. Their preferences, projects, and skills sync through your Anthropic account. Desktop MCP servers live in `%APPDATA%\Claude\claude_desktop_config.json` and often hold API keys, so they are not synced here.

## Gemini, ChatGPT, and the local vLLM

The files in `home/` are plain Markdown. You can paste `CLAUDE.md` into Gemini or ChatGPT custom instructions to keep one voice across tools. Claude Code does not use the vLLM server as its model; keep vLLM for local inference work.

## Obsidian vault sync

The vault syncs through its own private repository, not this one.

1. On GitHub, create an empty private repository, for example `heron301/obsidian-vault`.
2. On the XE3, install Git for Windows. In the vault folder (PowerShell):

   ```powershell
   cd "C:\Users\<you>\Documents\<VaultName>"
   git init -b main
   # Copy claude-config/obsidian/vault.gitignore here as .gitignore
   git add . ; git commit -m "Initial vault"
   git remote add origin git@github.com:heron301/obsidian-vault.git
   git push -u origin main
   ```

3. In Obsidian, install the community plugin **Git** (by Vinzent). Set auto commit-and-sync to 10 minutes and enable pull on startup.
4. On each other machine, clone the vault repository, open the folder as a vault in Obsidian, and enable the same plugin settings.
5. Keep your NAS backup of the vault on the XE3. Git gives history; the NAS gives an independent copy.

Large attachments (video, big PDFs) bloat a git repository. Keep them outside the vault or use Git LFS.
