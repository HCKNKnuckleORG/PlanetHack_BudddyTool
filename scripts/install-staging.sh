#!/usr/bin/env bash
# PlanetHack staging install for Ubuntu Server
# Usage: ./scripts/install-staging.sh [install_dir]
# Default: /opt/planethack

set -e
INSTALL_DIR="${1:-/opt/planethack}"
REPO_URL="${PLANETHACK_REPO:-}"

echo "[*] PlanetHack staging install -> $INSTALL_DIR"

sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv git nodejs npm

if [ -d .git ] && [ -f main.py ]; then
  echo "[*] Copying from current directory..."
  sudo mkdir -p "$INSTALL_DIR"
  sudo cp -a . "$INSTALL_DIR/"
  sudo chown -R "$USER:$USER" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
elif [ -n "$REPO_URL" ]; then
  echo "[*] Cloning from $REPO_URL..."
  sudo rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
else
  echo "[!] Run from repo root or set PLANETHACK_REPO" >&2
  exit 1
fi

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cd frontend && npm ci 2>/dev/null || npm install && npm run build && cd ..

[ -f config/config.yaml ] || cp config/config.example.yaml config/config.yaml

SVC="/etc/systemd/system/planethack.service"
echo "[Unit]
Description=PlanetHack Web UI
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python main.py --web
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target" | sudo tee "$SVC" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable planethack
echo "[*] Done. Start: sudo systemctl start planethack"
echo "[*] Update: cd $INSTALL_DIR && ./scripts/update.sh --restart"
