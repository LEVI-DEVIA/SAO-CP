# SAO-CP Backend API

This is the FastAPI backend that acts as the central hub for the SAO-CP project. It receives alerts from the AI Agent and streams them via WebSockets to the connected SOC Dashboards.

## Features
- **REST endpoints** for receiving and updating alerts.
- **WebSocket support** for real-time synchronization with frontend dashboards.

## How to run

We recommend using the root `Makefile`, but if you want to run it directly:

1. Make sure you have `uv` installed.
2. Run the server:
```bash
uv run uvicorn main:app --port 8000 --reload
```
The API will be accessible at `http://127.0.0.1:8000`.
You can access the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.
