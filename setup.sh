#!/bin/bash
# PlanetHack Setup - Check and optionally install required tools

echo ""
echo "========================================"
echo "  PLANET HACK - SETUP"
echo "========================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    exit 1
fi

echo "[*] Checking required tools..."
echo "[*] On Kali/Debian, you will be prompted to install missing tools via apt."
echo ""
python3 main.py --setup
echo ""
echo "[*] Done! Run ./launch.sh to choose Web, GUI, or CLI."
