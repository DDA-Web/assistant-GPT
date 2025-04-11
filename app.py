from flask import Flask, request, jsonify
import requests
import os
import time
import json
from dotenv import load_dotenv
import openai

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_4qIjf00E1XIYVvKV9GKAUzJp")

# Endpoints pour l'API externe
SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")

# Queue pour stocker les briefs en attente et terminés
pending_briefs = {}  # {id: {"keyword": keyword, "status": "pending"}}
completed_briefs = {}  # {id: {"keyword": keyword, "brief": brief_content, "status": "completed"}}

@app.route('/', methods=['GET'])
def index():
    """Route racine pour vérifier que l'API est en ligne"""
    return jsonify({
        "status": "API en ligne",
        "endpoints": [
            "/nouveauBrief",
            "/recupererBrief",
            "/enregistrerBrief",
            "/scrapeSERP",
            "/statut",
            "/process"
        ]
    }), 200

@app.route('/nouveauBrief', methods=['POST'])
def nouveau_brief():
    """Endpoint pour démarrer un nouveau brief à partir d'un mot-clé"""
    data = request.json
    if not data or not data.get('keyword'):
        return jsonify({"error": "Keyword is required"}), 400
    
    keyword = data.get('keyword')
    brief_id = f"brief_{int(time.time())}"  # ID unique basé sur le timestamp
    
    # Stocker le brief en attente
    pending_briefs[brief_id] = {
        "keyword": keyword,
        "status": "pending",
        "created_at": time.time()
    }
    
    # Lancer le processus de génération de brief de manière asynchrone
    # Dans une implémentation réelle, vous utiliseriez des tâches en arrière-plan
    # Ici, nous simulons simplement l'enqueue
    
    return jsonify({
        "status": "Brief en cours de traitement",
        "brief_id": brief_id,
        "keyword": keyword
    }), 202  # 202 Accepted

@app.route('/recupererBrief', methods=['GET'])
def recuperer_brief():
    """Récupérer le premier brief terminé disponible ou un brief spécifique"""
    brief_id = request.args.get('brief_id')
    keyword = request.args.get('keyword')
    
    if brief_id:
        # Récupérer un brief spécifique par ID
        if brief_id in completed_briefs:
            return jsonify(completed_briefs[brief_id]), 200
        elif brief_id in pending_briefs:
            return jsonify({
                "status": "pending",
                "brief_id": brief_id,
                "keyword": pending_briefs[brief_id]["keyword"]
            }), 202
        else:
            return jsonify({"error": "Brief not found"}), 404
    
    elif keyword:
        # Rechercher un brief par mot-clé
        matching_briefs = [b for b_id, b in completed_briefs.items() if b["keyword"] == keyword]
        if matching_briefs:
            return jsonify(matching_briefs[0]), 200
        else:
            return jsonify({"status": "No completed brief found for this keyword"}), 404
    
    else:
        # Récupérer le premier brief terminé disponible
        if not completed_briefs:
            return jsonify({"status": "No completed briefs available"}), 204  # No Content
        
        # Prendre le premier brief complété (le plus ancien)
        brief_id = next(iter(completed_briefs))
        brief_data = completed_briefs.pop(brief_id)  # Retire le brief de la liste des terminés
        
        return jsonify(brief_data), 200

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    """Enregistrer un brief généré"""
    data = request.json
    if not data or not data.get('keyword') or not data.get('brief'):
        return jsonify({"error": "Keyword and brief content are required"}), 400
    
    keyword = data.get('keyword')
    brief_content = data.get('brief')
    brief_id = data.get('brief_id', f"brief_{int(time.time())}")
    
    # Enregistrer le brief comme complété
    completed_briefs[brief_id] = {
        "keyword": keyword,
        "brief": brief_content,
        "status": "completed",
        "completed_at": time.time()
    }
    
    # Si ce brief était en attente, le retirer de la liste
    if brief_id in pending_briefs:
        del pending_briefs[brief_id]
    
    return jsonify({
        "status": "Brief enregistré avec succès",
        "brief_id": brief_id
    }), 200

@app.route('/scrapeSERP', methods=['GET'])
def scrape_serp():
    """Endpoint pour scraper les résultats SERP pour un mot-clé"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    try:
        response = requests.get(SERP_API_URL, params={'query': query}, timeout=30)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to scrape SERP: {str(e)}"}), 500

@app.route('/statut', methods=['GET'])
def statut():
    """Endpoint pour vérifier le statut de l'API"""
    return jsonify({
        "status": "online",
        "pending_briefs": len(pending_briefs),
        "completed_briefs": len(completed_briefs)
    }), 200

@app.route('/process', methods=['GET'])
def process_queue():
    """Endpoint pour traiter la file d'attente des briefs (normalement appelé par un cron job)"""
    if not pending_briefs:
        return jsonify({"status": "No pending briefs to process"}), 200
    
    # Prendre le premier brief en attente
    brief_id = next(iter(pending_briefs))
    brief_data = pending_briefs[brief_id]
    keyword = brief_data["keyword"]
    
    try:
        # Créer un thread OpenAI
        thread = openai.threads.create(assistant_id=ASSISTANT_ID)
        thread_id = thread.id
        
        # Ajouter le message avec le mot-clé
        openai.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"Générer un brief SEO pour le mot-clé: {keyword}"
        )
        
        # Lancer le run avec l'assistant
        run = openai.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=f"Génère un brief SEO complet pour le mot-clé '{keyword}'."
        )
        
        # Attendre et gérer l'exécution
        brief_content = handle_assistant_run(thread_id, run.id, keyword)
        
        # Enregistrer le brief comme complété
        completed_briefs[brief_id] = {
            "keyword": keyword,
            "brief": brief_content,
            "status": "completed",
            "completed_at": time.time()
        }
        
        # Retirer le brief de la liste des pending
        del pending_briefs[brief_id]
        
        return jsonify({
            "status": "Brief processed successfully",
            "brief_id": brief_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to process brief: {str(e)}",
            "brief_id": brief_id
        }), 500

def handle_assistant_run(thread_id, run_id, keyword):
    """Gérer l'exécution de l'assistant et récupérer le brief généré"""
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

def handle_tool_call(tool_call, keyword):
    """Gérer les appels d'outils de l'assistant"""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if function_name == "recupererBrief":
        # Simuler la récupération d'un brief existant
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps({"keyword": keyword, "status": "No existing brief found"})
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
        # Simuler l'enregistrement du brief
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps({"status": "Brief enregistré avec succès"})
        }
    
    else:
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps({"error": f"Fonction inconnue: {function_name}"})
        }

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=True, host='0.0.0.0', port=port)