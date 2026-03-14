.PHONY: help install run-web run-gui run-cli test lint build-docker clean

help:
	@echo "PlanetHack - Hack the Planet! 🌍"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run-web       - Run Web UI (http://localhost:8080)"
	@echo "  make run-gui       - Run GUI interface"
	@echo "  make run-cli       - Run CLI interface"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Lint code"
	@echo "  make build-docker  - Build Docker image"
	@echo "  make clean         - Clean build artifacts"
	@echo ""
	@echo "Or use: ./launch.sh for interactive menu"

install:
	pip install -r requirements.txt

run-web:
	python main.py --web

run-gui:
	python main.py --gui

run-cli:
	python main.py --cli

test:
	pytest tests/ -v --cov=python --cov-report=html

lint:
	flake8 python/
	black --check python/
	mypy python/ --ignore-missing-imports

build-docker:
	docker build -t planethack/ctf-tool:latest .

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info
	rm -rf logs/*.log

