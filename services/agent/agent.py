import os
import json
import requests
import asyncio
import ssl
import signal
from typing import TypedDict
from dotenv import load_dotenv

# Monkey-patch SSL to accept self-signed certificates BEFORE other imports
original_create_default_context = ssl.create_default_context

def create_unverified_context(*args, **kwargs):
    ctx = original_create_default_context(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

ssl.create_default_context = create_unverified_context

# Disable urllib3 warnings about insecure connections
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# MCP Adapter for LangChain
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

processed_events = set()  # Keep track of processed events to avoid duplicates


# ============================================
# 1. Agent State Definition
# ============================================
class AgentState(TypedDict):
    splunk_logs: str
    threat_detected: bool
    threat_details: str
    ai_proposal: str
    error: str
    alert_id: int

# ============================================
# 2. Initialize LLM (Gemma 4)
# ============================================
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

# ============================================
# 3. Graph Nodes Definition
# ============================================

async def fetch_splunk_logs(state: AgentState):
    """Node 1: Query Splunk via the Official MCP Server"""
    print("🔍 Node 1: Querying Splunk via official MCP Server...")
    
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
            return {"error": f"Tool 'splunk_run_query' not found. Available tools: {available}", "threat_detected": False}
        
        # Added earliest=-2m to only search the last 2 minutes
        spl_query = 'search index="main" action="UNAUTHORIZED_ACCESS_ATTEMPT" earliest=-2m | head 1'
        
        result = await search_tool.ainvoke({"query": spl_query})
        
        if result and len(result) > 0:
            text_content = result[0].get('text', '') if isinstance(result[0], dict) else str(result[0])
            
            try:
                splunk_data = json.loads(text_content)
                results = splunk_data.get('results', [])
                
                if results and len(results) > 0:
                    event = results[0]
                    event_id = event.get("_cd", event.get("_bkt", str(event.get("_indextime"))))
                    
                    if event_id in processed_events:
                        # print("   (Event already processed, skipping)")
                        return {"splunk_logs": "Attack already reported.", "threat_detected": False}
                    
                    processed_events.add(event_id)
                    print(f"🚨 New threat detected (ID: {event_id})!")
                    
                    logs_formatted = json.dumps(event, indent=2, ensure_ascii=False)
                    return {"splunk_logs": logs_formatted, "threat_detected": True}
                else:
                    return {"splunk_logs": "No attacks detected.", "threat_detected": False}
            except json.JSONDecodeError:
                return {"splunk_logs": text_content, "threat_detected": True}
        else:
            return {"splunk_logs": "No attacks detected.", "threat_detected": False}
            
    except Exception as e:
        return {"error": str(e), "threat_detected": False}


async def analyze_threat(state: AgentState):
    """Node 2: AI (Gemma 4) analyzes the log and proposes an action"""
    print("🧠 Node 2: Analyzing threat with AI...")
    
    logs = state.get('splunk_logs', 'No data')
    if not logs:
        logs = 'No data available'
    
    prompt = f"""You are an expert SOC analyst. A suspicious event has been detected in Splunk.
    Here is the raw data of the event:
    {logs}

    Analyze this event and propose ONE remediation action.
    Respond STRICTLY in JSON format, without any other text before or after:
    {{
        "reasoning": "Your analysis of the threat",
        "proposed_action": "BLOCK_IP or DISABLE_USER",
        "action_details": "Details of the action to execute"
    }}"""
            
    if not prompt or len(prompt.strip()) < 10:
        return {"threat_details": logs, "ai_proposal": "ERROR: Empty prompt"}
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    content = response.content
    if isinstance(content, list):
        content = " ".join([block.get('text', '') for block in content if isinstance(block, dict) and 'text' in block])
    
    print(f"  [DEBUG] Full AI Response:\n{content}\n")
    
    content_cleaned = content.strip()
    if content_cleaned.startswith("```json"):
        content_cleaned = content_cleaned[7:]
    if content_cleaned.endswith("```"):
        content_cleaned = content_cleaned[:-3]
    content_cleaned = content_cleaned.strip()
    
    try:
        proposal_json = json.loads(content_cleaned)
        ai_proposal_str = json.dumps(proposal_json, ensure_ascii=False)
    except json.JSONDecodeError as e:
        print(f"  [DEBUG] JSON parsing error ({e}). Attempting recovery with braces...")
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
    """Node 3: Send proposal to FastAPI Backend for human validation"""
    print("🚀 Node 3: Sending to SOC Dashboard for human validation...")
    
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
            data = response.json()
            print("✅ Alert sent to Dashboard!")
            # ✅ RETURN THE ALERT ID TO AVOID RE-SENDING IT IN THE NEXT CYCLE
            return {"alert_id": data.get("id"), "threat_detected": False}
        else:
            print(f"⚠️ Backend Error: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Backend unreachable: {e}")
        
    return {}


# ============================================
# 4. Build LangGraph Workflow (Detection Only)
# ============================================
workflow = StateGraph(AgentState)

workflow.add_node("fetch_logs", fetch_splunk_logs)
workflow.add_node("analyze", analyze_threat)
workflow.add_node("send_alert", send_to_dashboard)

workflow.set_entry_point("fetch_logs")

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
# 5. Execute Approved Actions Function
# ============================================
def check_pending_approvals():
    """Checks if a human has approved alerts and executes the actions"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/alerts")
        if response.status_code == 200:
            alerts = response.json()
            for alert in alerts:
                # If the alert is approved by the analyst, the agent executes it
                if alert.get("status") == "APPROVED":
                    print(f"\n⚡ EXECUTING ACTION: Alert {alert['id']} approved!")
                    print(f"   -> Action: {alert['proposed_action']} | Details: {alert['action_details']}")
                    
                    # HERE: You can add real execution code (e.g., call the CHU app API to block the IP)
                    # For the MVP, we simulate by changing the status to EXECUTED
                    
                    # Update status in FastAPI to avoid executing twice
                    requests.patch(f"http://127.0.0.1:8000/api/alerts/{alert['id']}?status=EXECUTED")
                    print("✅ Action executed successfully!\n")
                    
    except Exception as e:
        pass # Backend might not be running yet

# ============================================
# 6. Main Execution Loop
# ============================================
async def main():
    print("🤖 SAO-CP Agent Started (Official Splunk MCP Server + LangGraph)")
    print("🔗 Connecting to:", os.getenv("MCP_SPLUNK_SERVER_URL", "https://127.0.0.1:8089/services/mcp"))
    print("Press Ctrl+C to stop gracefully.\n")
    
    splunk_scan_interval = 15
    time_since_last_scan = 0
    
    try:
        while True:
            # 1. On vérifie les approbations en attente toutes les 2 secondes (Temps réel !)
            check_pending_approvals()
            await asyncio.sleep(2)
            time_since_last_scan += 2
            
            # 2. Tous les 15 secondes, on relance un cycle de détection Splunk
            if time_since_last_scan >= splunk_scan_interval:
                time_since_last_scan = 0
                
                initial_state = {
                    "splunk_logs": "",
                    "threat_detected": False,
                    "threat_details": "",
                    "ai_proposal": "",
                    "error": "",
                    "alert_id": None
                }
                
                try:
                    final_state = await app.ainvoke(initial_state)
                    
                    if final_state.get("error"):
                        print(f"❌ Error: {final_state['error']}")
                    elif not final_state.get("threat_detected"):
                        print("💤 No recent threats. Next scan in 15s...")
                    else:
                        print("🚨 Threat processed and sent to Dashboard!")
                        
                except Exception as e:
                    print(f"❌ Error during cycle execution: {e}")
            
    except KeyboardInterrupt:
        print("\n🛑 Agent shutdown requested. Closing connections... Bye!")

if __name__ == "__main__":
    asyncio.run(main())