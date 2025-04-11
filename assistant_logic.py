import os
import time
import json
import requests
import openai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_4qIjf00E1XIYVvKV9GKAUzJp")

# URL des endpoints
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")

def create_thread():
    """Créer un thread OpenAI"""
    thread = openai.threads.create(assistant_id=ASSISTANT_ID)
    return thread.id

def start_run(thread_id, keyword):
    """Lancer un run avec l'assistant"""
    # Ajouter le message avec le mot-clé
    openai.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=f"Générer un brief SEO pour le mot-clé: {keyword}"
    )
    
    # Lancer le run
    run = openai.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        instructions=f"Génère un brief SEO complet pour le mot-clé '{keyword}'."
    )
    return run.id

def handle_tool_call(tool_call, keyword):
    """Gérer les appels d'outils de l'assistant"""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if function_name == "recupererBrief":
        # Vérifier s'il existe déjà un brief pour ce mot-clé
        try:
            response = requests.get(f"{API_BASE_URL}/recupererBrief", 
                                   params={"keyword": keyword})
            if response.status_code == 200:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(response.json())
                }
            else:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": "No existing brief found"})
                }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps({"error": f"Exception during brief retrieval: {str(e)}"})
            }
    
    elif function_name == "getSERPResults":
        # Récupérer les résultats SERP
        query = arguments.get("query", keyword)
        try:
            response = requests.get(SERP_API_URL, params={"query": query}, timeout=30)
            if response.status_code == 200:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(response.json())
                }
            else:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": "Failed to scrape SERP", "status_code": response.status_code})
                }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps({"error": f"Exception during SERP scraping: {str(e)}"})
            }
    
    elif function_name == "enregistrerBrief":
        # Enregistrer le brief généré
        try:
            brief_content = arguments.get("brief", "")
            keyword = arguments.get("keyword", keyword)
            
            response = requests.post(f"{API_BASE_URL}/enregistrerBrief", 
                                    json={"keyword": keyword, "brief": brief_content})
            
            if response.status_code == 200:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": "Brief enregistré avec succès"})
                }
            else:
                return {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": "Failed to save brief", "status_code": response.status_code})
                }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "output": json.dumps({"error": f"Exception during brief saving: {str(e)}"})
            }
    
    else:
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps({"error": f"Fonction inconnue: {function_name}"})
        }

def run_brief_generation(keyword, brief_id=None):
    """Exécuter le processus complet de génération de brief"""
    # Créer un thread
    thread_id = create_thread()
    
    # Lancer le run
    run_id = start_run(thread_id, keyword)
    
    # Boucle d'attente pour les actions de l'assistant
    max_attempts = 30
    attempts = 0
    
    while attempts < max_attempts:
        try:
            run_status = openai.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            
            if run_status.status == "completed":
                # Récupérer les messages générés
                messages = openai.threads.messages.list(thread_id=thread_id)
                assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
                
                if assistant_messages:
                    # Prendre le dernier message de l'assistant
                    last_message = assistant_messages[0]
                    brief_content = last_message.content[0].text.value
                    
                    # Enregistrer le brief
                    save_data = {
                        "keyword": keyword,
                        "brief": brief_content
                    }
                    if brief_id:
                        save_data["brief_id"] = brief_id
                        
                    requests.post(f"{API_BASE_URL}/enregistrerBrief", json=save_data)
                    
                    return brief_content
                else:
                    return "Aucun brief généré."
            
            elif run_status.status == "requires_action":
                # Gérer les appels d'outils
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                outputs = [handle_tool_call(tc, keyword) for tc in tool_calls]
                
                openai.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=outputs
                )
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"Échec de la génération du brief: {run_status.status}"
                
            time.sleep(2)
            attempts += 1
            
        except Exception as e:
            return f"Erreur pendant la génération du brief: {str(e)}"
    
    return "Timeout pendant la génération du brief."

# Fonction pour traiter un brief de la file d'attente
def process_brief(brief_id, keyword):
    """Traiter un brief spécifique"""
    try:
        brief_content = run_brief_generation(keyword, brief_id)
        return {
            "status": "success",
            "brief_id": brief_id,
            "brief": brief_content
        }
    except Exception as e:
        return {
            "status": "error",
            "brief_id": brief_id,
            "error": str(e)
        }