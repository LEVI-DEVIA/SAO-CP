.PHONY: all install run-api run-agent run-soc-dashboard run-health-app help

help:
	@echo "SAO-CP Project Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install            - Install dependencies for all apps and services"
	@echo "  make run-api            - Run the FastAPI backend"
	@echo "  make run-agent          - Run the Python LangGraph AI Agent"
	@echo "  make run-soc-dashboard  - Run the SOC Dashboard Next.js app (Port 3000)"
	@echo "  make run-health-app     - Run the Health Next.js app (Port 3001)"

install:
	@echo "Installing frontend dependencies..."
	cd apps/soc-dashboard && npm install
	cd apps/health-app && npm install
	@echo "Installing backend dependencies..."
	cd services/api && uv sync
	cd services/agent && uv sync

run-api:
	@echo "Starting FastAPI backend..."
	cd services/api && uv run uvicorn main:app --port 8000 --reload

run-agent:
	@echo "Starting AI Agent..."
	cd services/agent && uv run python agent.py

run-soc-dashboard:
	@echo "Starting SOC Dashboard..."
	cd apps/soc-dashboard && npm run dev

run-health-app:
	@echo "Starting Health App..."
	cd apps/health-app && PORT=3001 npm run dev
