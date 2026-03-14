#!/bin/bash
# PlanetHack - Unified Launcher (Web / GUI / CLI, Local or Docker)

ensure_venv() {
    if ! command -v python3 &>/dev/null; then
        echo "[ERROR] Python 3 not found"
        return 1
    fi
    if [ ! -d "venv" ]; then
        echo "[*] Creating venv..."
        python3 -m venv venv
    fi
    source venv/bin/activate 2>/dev/null || true
    pip install -q -r requirements.txt 2>/dev/null || true
}

show_menu() {
    echo ""
    echo "========================================"
    echo "  PLANET HACK - HACK THE PLANET!"
    echo "========================================"
    echo ""
    echo "  How do you want to run PlanetHack?"
    echo ""
    echo "  LOCAL (Python venv):"
    echo "    1. Web UI    - Browser at http://localhost:8080"
    echo "    2. GUI       - Tkinter desktop app"
    echo "    3. CLI       - Interactive terminal"
    echo ""
    echo "  DOCKER (containerized):"
    echo "    4. Web UI    - docker-compose (browser at :8080)"
    echo "    5. CLI       - CLI inside container"
    echo ""
    echo "  WITH OLLAMA (AI-assisted next steps):"
    echo "    6. Web + Ollama (Python) - start Ollama + Web UI locally"
    echo "    7. Web + Ollama (Docker) - docker-compose with Ollama"
    echo ""
    echo "  SETUP:"
    echo "    8. Setup     - Check/install required tools"
    echo "    9. Exit"
    echo ""
    read -p "Enter choice (1-9): " choice
    echo ""

    case "$choice" in
        1)
            ensure_venv
            echo "[*] Starting Web UI... Open http://localhost:8080"
            python main.py --web
            ;;
        2)
            ensure_venv
            echo "[*] Starting GUI..."
            python main.py --gui
            ;;
        3)
            ensure_venv
            echo "[*] Starting CLI..."
            python main.py --cli
            ;;
        6)
            ./launch_web_with_ollama.sh
            ;;
        7)
            if ! docker info &>/dev/null; then
                echo "[ERROR] Docker is not running"
                read -p "Press Enter..."
                return
            fi
            echo "[*] Starting PlanetHack + Ollama (Docker)..."
            docker-compose -f docker-compose.yml -f docker-compose.ollama.yml --profile ollama up -d
            echo "[*] Web UI: http://localhost:8080"
            echo "[*] Ollama: http://localhost:11434"
            echo "[*] Pull model: docker exec planet-hack-ollama ollama pull llama3"
            read -p "Press Enter..."
            ;;
        4)
            if ! docker info &>/dev/null; then
                echo "[ERROR] Docker is not running"
                read -p "Press Enter..."
                return
            fi
            echo "[*] Starting containers (Web UI on port 8080)..."
            docker-compose up -d
            echo "[*] Web UI: http://localhost:8080"
            echo "[*] Stop: docker-compose down"
            read -p "Press Enter..."
            ;;
        5)
            if ! docker info &>/dev/null; then
                echo "[ERROR] Docker is not running"
                read -p "Press Enter..."
                return
            fi
            if ! docker-compose ps 2>/dev/null | grep -q planet-hack; then
                echo "[*] Starting containers first..."
                docker-compose up -d
            fi
            echo "[*] Launching CLI in container..."
            docker-compose exec planet-hack python main.py --cli
            read -p "Press Enter..."
            ;;
        8)
            if ! command -v python3 &>/dev/null; then
                echo "[ERROR] Python 3 not found"
            else
                python3 main.py --setup
            fi
            read -p "Press Enter..."
            ;;
        9)
            echo "Hack the Planet! 🌍"
            exit 0
            ;;
        *)
            echo "Invalid choice!"
            sleep 2
            ;;
    esac
}

while true; do
    show_menu
done
