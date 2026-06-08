from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI(title="SAO-CP Backend")

# Allow Next.js frontends to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for security alerts
class AlertPayload(BaseModel):
    id: Optional[int] = None
    agent_id: str
    threat_type: str
    threat_data: str
    ai_reasoning: str
    proposed_action: str
    action_details: str
    status: str = "PENDING_HUMAN_APPROVAL"

# In-memory database for the hackathon MVP
alerts_db: List[AlertPayload] = []
# Keep track of active dashboard connections for real-time updates
connected_dashboards: List[WebSocket] = []

@app.get("/api/alerts/{alert_id}")
async def get_alert_status(alert_id: int):
    """Agent use this endpoint to check status of an alert after submission."""
    if alert_id < len(alerts_db):
        return alerts_db[alert_id]
    return {"error": "Not found"}


@app.post("/api/alerts")
async def receive_alert(alert: AlertPayload):
    """Receive an alert from the AI agent and broadcast it to connected dashboards."""
    alert.id = len(alerts_db)
    
    print(f"🚨 Received alert from {alert.agent_id}: {alert.threat_type}")
    
    # 1. Save the alert
    alerts_db.append(alert)
    
    # 2. Broadcast to all connected SOC Dashboards
    for dashboard in connected_dashboards:
        try:
            await dashboard.send_text(alert.json())
        except Exception:
            pass
            
    return {"message": "Alert received", "id": alert.id}


@app.patch("/api/alerts/{alert_id}")
async def update_alert_status(alert_id: int, status: str):
    """Update alert status (e.g., APPROVED or REJECTED) when a human reviews it."""
    if alert_id >= len(alerts_db):
        return {"error": "Alert not found"}
    
    # Update the status
    alerts_db[alert_id].status = status
    print(f"✅ Alert {alert_id} updated: {status}")
    
    # Notify all dashboards about the change
    updated_alert = alerts_db[alert_id]
    for dashboard in connected_dashboards:
        try:
            await dashboard.send_text(updated_alert.json())
        except Exception:
            pass
            
    return {"message": "Status updated", "alert": updated_alert}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time SOC dashboard updates."""
    await websocket.accept()
    connected_dashboards.append(websocket)
    print("🛡️ A SOC Dashboard connected")
    
    # Send historical alerts to the newly connected dashboard
    for alert in alerts_db:
        await websocket.send_text(alert.json())
    
    try:
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connected_dashboards.remove(websocket)
        print("👋 A SOC Dashboard disconnected")

@app.get("/api/alerts")
async def get_alerts():
    """Get all alerts (useful for debugging and polling)."""
    return alerts_db