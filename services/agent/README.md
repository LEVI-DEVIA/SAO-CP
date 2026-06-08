# SAO-CP AI Agent

This folder contains the LangGraph + LangChain agent for the SAO-CP ecosystem.

## Features
- Periodically queries the official Splunk MCP server to fetch recent logs.
- Detects security threats (e.g., unauthorized access).
- Uses Google Gemini to propose actionable remediations.
- Forwards proposals to the FastAPI backend.
- Polls the backend to execute the remediation once approved by a human operator.

## Configuration
Ensure you have a `.env` file in this folder with the following variables:
```env
GOOGLE_API_KEY=your_gemini_api_key
SPLUNK_MCP_TOKEN=your_splunk_mcp_token
MCP_SPLUNK_SERVER_URL=https://127.0.0.1:8089/services/mcp
FASTAPI_BACKEND_URL=http://127.0.0.1:8000/api/alerts
```

## How to run

We recommend using the root `Makefile`, but if you want to run it directly:

1. Make sure you have `uv` installed.
2. Run the agent:
```bash
uv run python agent.py
```