import os
import json
import requests
import asyncio
import ssl
import signal
from typing import TypedDict
from dotenv import load_dotenv

# Monkey-patch SSL pour accepter les certificats auto-signés AVANT les imports
original_create_default_context = ssl.create_default_context

def create_unverified_context(*args, **kwargs):
    ctx = original_create_default_context(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

ssl.create_default_context = create_unverified_context

# Désactiver les avertissements urllib3
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# LangGraph & LangChain
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# MCP Adapter pour LangChain
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

processed_events = set()  # Pour éviter de traiter plusieurs fois le même événement

# ============================================
# 1. Définition de l'état (State) de l'Agent
# ============================================
class AgentState(TypedDict):
    splunk_logs: str
    threat_detected: bool
    threat_details: str
    ai_proposal: str
    error: str

# ============================================
# 2. Initialisation du LLM (Gemma 4)
# ============================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ============================================
# 3. Définition des Nœuds (Nodes) du Graphe
# ============================================

async def fetch_splunk_logs(state: AgentState):
    """Nœud 1: Utilise le Splunk MCP Server OFFICIEL"""
    print("🔍 Nœud 1 : Interrogation de Splunk via le MCP Server officiel...")
    
    try:
        client = MultiServerMCPClient(
            connections={
                "splunk": {
                    "transport": "http",
                    "url": os.getenv("MCP_SPLUNK_SERVER_URL", "https://127.0.0.1:8089/services/mcp"),
                    "headers": {
                        "Authorization": f"Bearer {os.getenv('SPLUNK_MCP_TOKEN')}"
                    },
                }
            }
        )
        
        mcp_tools = await client.get_tools()
        search_tool = next((tool for tool in mcp_tools if tool.name == "splunk_run_query"), None)
        
        if not search_tool:
            available = [t.name for t in mcp_tools]
            return {"error": f"Outil introuvable. Disponibles: {available}", "threat_detected": False}
        
        spl_query = 'search index="main" action="UNAUTHORIZED_ACCESS_ATTEMPT" earliest=-2m | head 1'
        
        result = await search_tool.ainvoke({"query": spl_query})
        
        if result and len(result) > 0:
            text_content = result[0].get('text', '') if isinstance(result[0], dict) else str(result[0])
            
            # try:
            #     splunk_data = json.loads(text_content)
            #     results = splunk_data.get('results', [])
                
            #     if results and len(results) > 0:
            #         print("🚨 Menace détectée dans Splunk !")
            #         logs_formatted = json.dumps(results[0], indent=2, ensure_ascii=False)
            #         return {"splunk_logs": logs_formatted, "threat_detected": True}
            #     else:
            #         return {"splunk_logs": "Aucune attaque détectée.", "threat_detected": False}
            # except json.JSONDecodeError:
            #     return {"splunk_logs": text_content, "threat_detected": True}

            try:
                splunk_data = json.loads(text_content)
                results = splunk_data.get('results', [])
                
                if results and len(results) > 0:
                    event = results[0]
                    
                    # L'identifiant unique de l'événement dans Splunk
                    event_id = event.get("_cd", event.get("_bkt", str(event.get("_indextime"))))
                    
                    # VÉRIFICATION
                    if event_id in processed_events:
                        # print("   (Événement déjà traité, on ignore)") # Optionnel
                        return {"splunk_logs": "Attaque déjà signalée.", "threat_detected": False}
                    
                    # Sinon, on le marque comme traité
                    processed_events.add(event_id)
                    print(f"🚨 Nouvelle menace détectée (ID: {event_id}) !")
                    
                    logs_formatted = json.dumps(event, indent=2, ensure_ascii=False)
                    return {"splunk_logs": logs_formatted, "threat_detected": True}
                else:
                    return {"splunk_logs": "Aucune attaque détectée.", "threat_detected": False}
            except json.JSONDecodeError:
                return {"splunk_logs": text_content, "threat_detected": True}

        else:
            return {"splunk_logs": "Aucune attaque détectée.", "threat_detected": False}
            
    except Exception as e:
        return {"error": str(e), "threat_detected": False}


async def analyze_threat(state: AgentState):
    """Nœud 2: L'IA (Gemma 4) analyse le log et propose une action"""
    print("🧠 Nœud 2 : Analyse de la menace par l'IA...")
    
    logs = state.get('splunk_logs', 'Aucune donnée')
    if not logs:
        logs = 'Aucune donnée disponible'
    
    prompt = f"""Tu es un analyste SOC expert. Un événement suspect a été détecté dans Splunk.
        Voici les données brutes de l'événement :
        {logs}

        Analyse cet événement et propose UNE SEULE action de remédiation.
        Réponds STRICTEMENT au format JSON, sans aucun autre texte avant ou après :
        {{
            "reasoning": "Ton analyse de la menace",
            "proposed_action": "BLOCK_IP ou DISABLE_USER",
            "action_details": "Détails de l'action à exécuter"
        }}"""
                    
    if not prompt or len(prompt.strip()) < 10:
        return {"threat_details": logs, "ai_proposal": "ERROR: Empty prompt"}
    
    # Appel à l'IA
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    # 1. Extraire le texte proprement
    content = response.content
    if isinstance(content, list):
        # Si LangChain renvoie une liste de blocs, on concatène le texte
        content = " ".join([block.get('text', '') for block in content if isinstance(block, dict) and 'text' in block])
    
    # 2. Afficher TOUTE la réponse sans la couper (fin du problème entrecoupé !)
    print(f"  [DEBUG] Réponse complète de l'IA :\n{content}\n")
    
    # 3. Nettoyer le formatage Markdown que l'IA ajoute parfois (ex: ```json ... ```)
    content_cleaned = content.strip()
    if content_cleaned.startswith("```json"):
        content_cleaned = content_cleaned[7:]
    if content_cleaned.endswith("```"):
        content_cleaned = content_cleaned[:-3]
    content_cleaned = content_cleaned.strip()
    
    # 4. Parser le JSON
    try:
        proposal_json = json.loads(content_cleaned)
        ai_proposal_str = json.dumps(proposal_json, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"  [DEBUG] Erreur de parsing JSON ({e}). Tentative de récupération avec les accolades...")
        # Plan B : chercher la première et la dernière accolade
        start_idx = content_cleaned.find('{')
        end_idx = content_cleaned.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            try:
                proposal_json = json.loads(content_cleaned[start_idx:end_idx])
                ai_proposal_str = json.dumps(proposal_json, ensure_ascii=False)
            except:
                ai_proposal_str = content_cleaned
        else:
            ai_proposal_str = content_cleaned

    return {"threat_details": state['splunk_logs'], "ai_proposal": ai_proposal_str}


async def send_to_dashboard(state: AgentState):
    """Nœud 3: Envoie la proposition au Backend FastAPI pour validation humaine"""
    print("🚀 Nœud 3 : Envoi au Dashboard SOC pour validation humaine...")
    
    try:
        proposal = json.loads(state['ai_proposal'])
    except:
        proposal = {"raw_proposal": state['ai_proposal']}

    payload = {
        "agent_id": "SAO-CP-LangGraph-Agent",
        "threat_type": "Unauthorized Access",
        "threat_data": state['threat_details'],
        "ai_reasoning": proposal.get("reasoning", "N/A"),
        "proposed_action": proposal.get("proposed_action", "REVIEW_MANUALLY"),
        "action_details": proposal.get("action_details", "N/A"),
        "status": "PENDING_HUMAN_APPROVAL"
    }
    
    try:
        response = requests.post(
            os.getenv("FASTAPI_BACKEND_URL", "http://127.0.0.1:8000/api/alerts"),
            json=payload
        )
        if response.status_code == 200:
            print("✅ Alerte envoyée au Dashboard !")
        else:
            print(f"⚠️ Erreur Backend: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Backend injoignable: {e}")
        
    return {}


# ============================================
# 4. Construction du Graphe LangGraph
# ============================================
workflow = StateGraph(AgentState)

workflow.add_node("fetch_logs", fetch_splunk_logs)
workflow.add_node("analyze", analyze_threat)
workflow.add_node("send_alert", send_to_dashboard)

workflow.set_entry_point("fetch_logs")

# Condition : si menace détectée → analyser, sinon → fin
workflow.add_conditional_edges(
    "fetch_logs",
    lambda state: "analyze" if state.get("threat_detected") else END,
    {
        "analyze": "analyze",
        END: END
    }
)

workflow.add_edge("analyze", "send_alert")
workflow.add_edge("send_alert", END)

app = workflow.compile()

# ============================================
# 5. Boucle d'exécution principale
# ============================================
async def main():
    print("🤖 Agent SAO-CP Démarré (Splunk MCP Server officiel + LangGraph)")
    print("🔗 Connexion à:", os.getenv("MCP_SPLUNK_SERVER_URL", "https://127.0.0.1:8089/services/mcp"))
    print("Appuyez sur Ctrl+C pour arrêter proprement.\n")
    
    try:
        while True:
            initial_state = {
                "splunk_logs": "",
                "threat_detected": False,
                "threat_details": "",
                "ai_proposal": "",
                "error": ""
            }
            
            try:
                final_state = await app.ainvoke(initial_state)
                
                if final_state.get("error"):
                    print(f"❌ Erreur: {final_state['error']}")
                elif not final_state.get("threat_detected"):
                    print("💤 Aucune menace récente. Nouveau scan dans 15s...")
                else:
                    print("🚨 Menace traitée et envoyée au Dashboard !")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'exécution du cycle: {e}")
                
            await asyncio.sleep(15)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'agent demandé. Fermeture des connexions... Ciao !")

if __name__ == "__main__":
    asyncio.run(main())