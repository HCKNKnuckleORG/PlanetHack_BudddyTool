#!/usr/bin/env bash
# PlanetHack self-update script for Ubuntu staging
# Run from project root. Requires git.
#
# Usage:
#   ./scripts/update.sh              # pull, install deps, build frontend
#   ./scripts/update.sh --restart    # also restart systemd service

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[*] PlanetHack update - $(date)"
echo "[*] Working directory: $ROOT"

# Git pull
if [[ -d .git ]]; then
  echo "[*] Pulling from git..."
  git pull
  echo "[*] Git pull done"
else
  echo "[!] Not a git repo, skipping pull"
fi

# Python deps
if [[ -d venv ]]; then
  echo "[*] Activating venv and installing Python deps..."
  . venv/bin/activate
  pip install -q -r requirements.txt
else
  echo "[*] Installing Python deps (no venv)..."
  pip install -q -r requirements.txt
fi

# Frontend build
if [[ -d frontend ]] && [[ -f frontend/package.json ]]; then
  echo "[*] Building frontend..."
  (cd frontend && npm ci --silent 2>/dev/null || npm install --silent) && npm run build
  echo "[*] Frontend build done"
else
  echo "[!] No frontend dir, skipping"
fi

# Optional: restart systemd service
if [[ "${1:-}" == "--restart" ]]; then
  if systemctl is-active --quiet planethack 2>/dev/null; then
    echo "[*] Restarting planethack service..."
    sudo systemctl restart planethack
    echo "[*] Service restarted"
  else
    echo "[!] planethack service not found or not active, skipping restart"
  fi
fi

VERSION=$(cat VERSION 2>/dev/null || echo "?")
echo "[+] Update complete. Version: $VERSION"
