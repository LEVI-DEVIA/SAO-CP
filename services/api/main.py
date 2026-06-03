from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json

app = FastAPI(title="SAO-CP Backend")

# Autoriser le frontend Next.js à communiquer avec ce backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de données pour l'alerte
class AlertPayload(BaseModel):
    id: Optional[int] = None
    agent_id: str
    threat_type: str
    threat_data: str
    ai_reasoning: str
    proposed_action: str
    action_details: str
    status: str = "PENDING_HUMAN_APPROVAL"

# Base de données en mémoire (pour le MVP du hackathon)
alerts_db: List[AlertPayload] = []
# Liste des dashboards connectés en temps réel
connected_dashboards: List[WebSocket] = []

@app.post("/api/alerts")
async def receive_alert(alert: AlertPayload):
    """Reçoit l'alerte de l'Agent LangGraph et la diffuse aux dashboards"""
    alert.id = len(alerts_db)
    
    print(f"🚨 Alerte reçue de {alert.agent_id} : {alert.threat_type}")
    
    # 1. Sauvegarder l'alerte
    alerts_db.append(alert)
    
    # 2. Envoyer l'alerte en temps réel à tous les Dashboards SOC connectés
    for dashboard in connected_dashboards:
        try:
            await dashboard.send_text(alert.json())
        except Exception:
            pass
            
    return {"message": "Alert received", "id": alert.id}


@app.patch("/api/alerts/{alert_id}")
async def update_alert_status(alert_id: int, status: str):
    """Mise à jour du statut (APPROVED ou REJECTED) par l'humain"""
    if alert_id >= len(alerts_db):
        return {"error": "Alert not found"}
    
    # Mettre à jour le statut
    alerts_db[alert_id].status = status
    print(f"✅ Alerte {alert_id} mise à jour : {status}")
    
    # Diffuser la mise à jour à tous les Dashboards
    updated_alert = alerts_db[alert_id]
    for dashboard in connected_dashboards:
        try:
            await dashboard.send_text(updated_alert.json())
        except Exception:
            pass
            
    return {"message": "Status updated", "alert": updated_alert}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour le Dashboard SOC (temps réel)"""
    await websocket.accept()
    connected_dashboards.append(websocket)
    print("🛡️ Un Dashboard SOC s'est connecté")
    
    # Envoyer l'historique des alertes au nouveau dashboard
    for alert in alerts_db:
        await websocket.send_text(alert.json())
    
    try:
        while True:
            # Garder la connexion ouverte
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connected_dashboards.remove(websocket)
        print("👋 Un Dashboard SOC s'est déconnecté")

@app.get("/api/alerts")
async def get_alerts():
    """Récupérer toutes les alertes (utile pour le debug)"""
    return alerts_db