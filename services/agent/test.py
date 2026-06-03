# import asyncio
# import os
# from dotenv import load_dotenv
# from langchain_mcp_adapters.client import MultiServerMCPClient

# load_dotenv()

# async def test_mcp_connection():
#     print("🔍 Tentative de connexion au Splunk MCP Server...")
    
#     async with MultiServerMCPClient(
#         connections={
#             "splunk": {
#                 "transport": "http",
#                 "url": os.getenv("SPLUNK_MCP_URL", "https://127.0.0.1:8089/services/mcp"),
#                 "headers": {
#                     "Authorization": f"Bearer {os.getenv('SPLUNK_MCP_TOKEN')}"
#                 },
#                 "tls_verify": False, # Très important pour Splunk local
#             }
#         }
#     ) as client:
#         print("✅ Connecté au serveur MCP !")
        
#         # 1. Vérifier les outils découverts
#         mcp_tools = client.get_tools()
#         print(f"\n🛠️ Outils découverts via MCP ({len(mcp_tools)}) :")
#         for tool in mcp_tools:
#             print(f"  - {tool.name}")
        
#         # 2. Chercher l'outil spécifique de recherche
#         search_tool = next((tool for tool in mcp_tools if tool.name == "splunk_run_query"), None)
        
#         if not search_tool:
#             print("\n❌ Outil 'splunk_run_query' introuvable. Vérifie l'installation du MCP dans Splunk.")
#             return
        
#         print("\n🚀 L'outil 'splunk_run_query' a été trouvé !")
#         print("⏳ Exécution de la requête SPL pour trouver l'attaque simulée...")
        
#         # 3. Exécuter la requête SPL
#         # On cherche l'action générée par ton bouton rouge
#         spl_query = 'search index="main" action="UNAUTHORIZED_ACCESS_ATTEMPT" | head 1'
        
#         try:
#             result = await search_tool.ainvoke({"query": spl_query})
            
#             print("\n" + "="*50)
#             if result and "No results" not in str(result) and result.strip():
#                 print("🎉 SUCCÈS ! L'agent a détecté le log d'attaque dans Splunk :")
#                 print(result)
#             else:
#                 print("💤 Aucune attaque trouvée. As-tu bien cliqué sur le bouton rouge dans l'app Next.js ?")
#             print("="*50)
            
#         except Exception as e:
#             print(f"\n❌ Erreur lors de la recherche SPL : {e}")

# if __name__ == "__main__":
#     asyncio.run(test_mcp_connection())













import asyncio
import os
import ssl
from dotenv import load_dotenv

# Monkey-patch SSL pour accepter les certificats auto-signés
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

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

async def main():
    client = MultiServerMCPClient(
        {
            "splunk": {
                "transport": "http",
                "url": os.getenv("MCP_SPLUNK_SERVER_URL", "https://127.0.0.1:8089/services/mcp"),
                "headers": {
                    "Authorization": f"Bearer {os.getenv('SPLUNK_MCP_TOKEN')}"
                },
            }
        }
    )

    print("✅ Connexion au serveur MCP établie avec succès!")
    
    try:
        tools = await client.get_tools()
        print(f"✅ {len(tools)} outil(s) MCP découvert(s):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement des outils: {e}")
        return
    
    print("\n✅ Test MCP réussi!")

if __name__ == "__main__":
    asyncio.run(main())
