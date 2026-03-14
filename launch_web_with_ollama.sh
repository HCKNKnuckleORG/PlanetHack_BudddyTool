#!/bin/bash
# PlanetHack Web UI + Ollama - Run both when using Python locally
# Ollama must be installed: https://ollama.ai

echo ""
echo "========================================"
echo "  PLANET HACK - WEB UI + OLLAMA"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found"
    exit 1
fi

# Check Ollama
if command -v ollama &>/dev/null; then
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        echo "[*] Starting Ollama in background..."
        ollama serve &
        sleep 3
    else
        echo "[*] Ollama already running at http://localhost:11434"
    fi
    export OLLAMA_URL=http://localhost:11434
else
    echo "[WARN] Ollama not found. Install from https://ollama.ai"
    echo "[*] Starting Web UI only. AI features will be disabled."
fi

# venv
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate 2>/dev/null || true
pip install -q -r requirements.txt

echo "[*] Launching PlanetHack Web UI..."
echo "[*] Open http://localhost:8080"
echo "[*] Press Ctrl+C to stop"
echo ""
python3 main.py --web
