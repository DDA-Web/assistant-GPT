import os
import time
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from urllib.parse import urlparse

# Charger les variables d'environnement
load_dotenv()

# Configuration OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = "asst_4qIjf00E1XIYVvKV9GKAUzJp"  # ID de votre Assistant GPT

app = Flask(__name__)

# Files d'attente pour les briefs
pending_briefs = {}     # Format : {brief_id: {"keyword": keyword, "status": "pending", "created_at": timestamp}}
completed_briefs = {}   # Format : {brief_id: {"keyword": keyword, "brief": brief, "status": "completed", "completed_at": timestamp}}

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "API en ligne",
        "endpoints": [
            "/nouveauBrief",
            "/recupererBrief",
            "/enregistrerBrief",
            "/getSERPResults",
            "/process",
            "/statut"
        ]
    }), 200

@app.route('/nouveauBrief', methods=['POST'])
def nouveau_brief():
    """
    Endpoint appelé par Make pour ajouter un nouveau mot-clé à traiter.
    """
    data = request.json
    if not data or not data.get('keyword'):
        return jsonify({"error": "Keyword is required"}), 400

    keyword = data.get('keyword')
    brief_id = f"brief_{int(time.time())}"
    pending_briefs[brief_id] = {
        "keyword": keyword,
        "status": "pending",
        "created_at": time.time()
    }
    return jsonify({
        "status": "Brief en cours de traitement",
        "brief_id": brief_id,
        "keyword": keyword
    }), 202

@app.route('/recupererBrief', methods=['GET'])
def recuperer_brief():
    """
    Endpoint pour récupérer un brief.
    """
    brief_id = request.args.get('brief_id')
    keyword = request.args.get('keyword')

    # Si l'appel spécifie un brief_id précis
    if brief_id:
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

    # Si l'appel spécifie un keyword précis
    elif keyword:
        matching = [b for b in completed_briefs.values() if b["keyword"] == keyword]
        if matching:
            return jsonify(matching[0]), 200
        else:
            return jsonify({"status": "No completed brief found for this keyword"}), 404

    # Sans paramètres, retourner le premier brief en attente
    else:
        if pending_briefs:
            brief_id = next(iter(pending_briefs))
            return jsonify({
                "keyword": pending_briefs[brief_id]["keyword"]
            }), 200
        else:
            return jsonify({"status": "No pending briefs"}), 204

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    """
    Endpoint pour enregistrer un brief généré.
    """
    data = request.json
    if not data or not data.get('keyword') or not data.get('brief'):
        return jsonify({"error": "Keyword and brief content are required"}), 400

    keyword = data.get('keyword')
    brief_content = data.get('brief')
    
    # Chercher le brief_id correspondant au keyword dans les pending_briefs
    matching_brief_ids = [bid for bid, bdata in pending_briefs.items() if bdata["keyword"] == keyword]
    
    if matching_brief_ids:
        brief_id = matching_brief_ids[0]
    else:
        brief_id = f"brief_{int(time.time())}"
    
    completed_briefs[brief_id] = {
        "keyword": keyword,
        "brief": brief_content,
        "status": "completed",
        "completed_at": time.time()
    }
    
    if brief_id in pending_briefs:
        del pending_briefs[brief_id]
    
    return jsonify({
        "status": "Brief enregistré avec succès",
        "brief_id": brief_id
    }), 200

def get_serp_data_for_keyword(keyword):
    """
    Fonction interne pour récupérer les données SERP pour un mot-clé,
    avec un formatage amélioré pour l'analyse concurrentielle.
    """
    try:
        SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")
        response = requests.get(SERP_API_URL, params={"query": keyword}, timeout=30)
        response.raise_for_status()
        
        serp_data = response.json()
        
        # Formater les données pour l'Assistant
        formatted_data = {
            "query": keyword,
            "organic_results": [],
            "related_searches": [],
            "related_questions": []
        }
        
        # Extraire et améliorer les résultats organiques
        if "results" in serp_data and isinstance(serp_data["results"], list):
            enhanced_results = []
            
            for idx, result in enumerate(serp_data["results"][:10]):  # Limiter aux 10 premiers
                # Extraire le domaine si nécessaire
                domain = result.get("domain", "")
                if not domain and "url" in result:
                    try:
                        parsed_url = urlparse(result["url"])
                        domain = parsed_url.netloc
                    except:
                        pass
                
                # S'assurer que word_count est bien présent
                word_count = result.get("word_count", "N/A")
                
                # Améliorer les informations sur les médias
                media_info = result.get("media", {})
                images = media_info.get("images", 0)
                videos = media_info.get("videos", 0)
                
                # Créer un résultat amélioré
                enhanced_result = dict(result)  # Copier toutes les données originales
                
                # Ajouter ou améliorer certains champs
                enhanced_result["domain"] = domain or "N/A"
                enhanced_result["word_count"] = word_count
                enhanced_result["media_summary"] = {
                    "images_count": images,
                    "videos_count": videos,
                    "has_media": (images > 0 or videos > 0)
                }
                enhanced_result["position"] = idx + 1
                
                enhanced_results.append(enhanced_result)
            
            formatted_data["organic_results"] = enhanced_results
        
        # Extraire les recherches associées
        if "associated_searches" in serp_data and isinstance(serp_data["associated_searches"], list):
            formatted_data["related_searches"] = serp_data["associated_searches"]
        
        # Extraire les questions PAA (People Also Ask)
        if "paa_questions" in serp_data and isinstance(serp_data["paa_questions"], list):
            formatted_data["related_questions"] = [{"question": q} for q in serp_data["paa_questions"]]
        
        return formatted_data
    except Exception as e:
        print(f"Error getting SERP data for keyword '{keyword}': {str(e)}")
        return {"query": keyword, "error": str(e)}

@app.route('/getSERPResults', methods=['GET'])
def get_serp_results():
    """
    Endpoint appelé par l'Assistant GPT pour obtenir les données SERP.
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # Utiliser la fonction améliorée
        formatted_data = get_serp_data_for_keyword(query)
        print(f"SERP data for query '{query}': {formatted_data}")
        
        return jsonify(formatted_data), 200
    except Exception as e:
        print(f"Unexpected error in getSERPResults: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def generate_brief_with_assistant(keyword, serp_data):
    """
    Génère un brief SEO en utilisant l'assistant OpenAI existant.
    Compatible avec openai v1.x et gère les états requires_action.
    """
    try:
        # Importer OpenAI ici pour éviter les problèmes de configuration globale
        import openai
        from openai import OpenAI
        
        # Créer le client sans proxy
        client = OpenAI(api_key=API_KEY)
        
        # 1. Créer une conversation (thread)
        thread = client.beta.threads.create()
        thread_id = thread.id
        
        # 2. Préparer un message avec les instructions et les données SERP
        message_content = f"Génère un brief SEO pour le mot-clé '{keyword}' en suivant le canevas fourni. Voici les données SERP:"
        
        # Ajouter des instructions pour l'analyse concurrentielle
        message_content += """

IMPORTANT: Pour l'analyse concurrentielle (section II.1), assure-toi d'inclure les informations suivantes pour chaque résultat:
- Domaine: disponible dans le champ "domain"
- Titre: disponible dans le champ "page_title"
- Volumétrie: disponible dans le champ "word_count" (nombre de mots)
- Médias: indique le nombre d'images et de vidéos (champs "media.images" et "media.videos")
- Données structurées: indique si présentes (champ "structured_data")

Pour chaque résultat, identifie également au moins une force et une faiblesse.
"""
        
        # Ajouter les résultats organiques
        if "organic_results" in serp_data and serp_data["organic_results"]:
            message_content += "\n\n## Top résultats Google:"
            for result in serp_data["organic_results"][:10]:
                position = result.get("position", "N/A")
                title = result.get("page_title", "")
                url = result.get("url", "")
                description = result.get("meta_description", "")
                domain = result.get("domain", "")
                word_count = result.get("word_count", "N/A")
                media_info = result.get("media_summary", {})
                
                message_content += f"\n{position}. {title}"
                message_content += f"\n   URL: {url}"
                message_content += f"\n   Description: {description}"
                message_content += f"\n   Domaine: {domain}"
                message_content += f"\n   Volumétrie: {word_count} mots"
                message_content += f"\n   Médias: Images: {media_info.get('images_count', 0)}, Vidéos: {media_info.get('videos_count', 0)}"
                message_content += "\n"
        
        # Ajouter les recherches associées
        if "related_searches" in serp_data and serp_data["related_searches"]:
            message_content += "\n\n## Recherches associées:"
            for search in serp_data["related_searches"]:
                message_content += f"\n- {search}"
        
        # Ajouter les questions fréquentes
        if "related_questions" in serp_data and serp_data["related_questions"]:
            message_content += "\n\n## Questions fréquentes:"
            for question in serp_data["related_questions"]:
                message_content += f"\n- {question.get('question', '')}"
        
        # 3. Ajouter le message au thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_content
        )
        
        # 4. Exécuter l'assistant sur le thread
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # 5. Attendre que l'assistant termine son travail
        run_status = run.status
        run_id = run.id
        
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            time.sleep(3)  # Attendre pour éviter trop de requêtes
            
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            run_status = run.status
            print(f"Run status: {run_status}")
            
            if run_status == "completed":
                break
            elif run_status == "requires_action":
                # Gérer l'action requise - approuver automatiquement les fonctions
                try:
                    required_actions = run.required_action
                    if required_actions and required_actions.type == "submit_tool_outputs":
                        tool_calls = required_actions.submit_tool_outputs.tool_calls
                        tool_outputs = []
                        
                        print(f"Assistant requires action with {len(tool_calls)} tool calls")
                        
                        for tool_call in tool_calls:
                            tool_call_id = tool_call.id
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            print(f"Tool call: {function_name} with args: {function_args}")
                            
                            # Traiter l'appel de fonction et obtenir un résultat
                            result = {}
                            
                            if function_name == "getSERPResults":
                                query = function_args.get("query", keyword)
                                serp_result = get_serp_data_for_keyword(query)
                                result = serp_result
                            elif function_name == "recupererBrief":
                                # Retourner un résultat vide, car l'assistant a déjà les données nécessaires
                                result = {"keyword": keyword}
                            elif function_name == "enregistrerBrief":
                                # Ne rien faire ici, car l'enregistrement se fera après la génération complète
                                result = {"status": "success"}
                            
                            # Convertir le résultat en JSON
                            output = json.dumps(result)
                            
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": output
                            })
                        
                        # Soumettre les réponses aux appels de fonction
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run_id,
                            tool_outputs=tool_outputs
                        )
                        
                        print(f"Submitted {len(tool_outputs)} tool outputs")
                        
                    else:
                        print("Required action of unknown type")
                        raise Exception(f"Unknown required action type: {required_actions.type}")
                except Exception as e:
                    print(f"Error handling requires_action: {str(e)}")
                    raise e
            elif run_status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Assistant run failed with status: {run_status}")
            
            if run_status not in ["completed", "requires_action", "in_progress", "queued"]:
                raise Exception(f"Unexpected status: {run_status}")
            
            if attempt >= max_attempts:
                raise Exception(f"Reached maximum attempts. Last status: {run_status}")
        
        # 6. Récupérer la réponse de l'assistant
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        # Récupérer la dernière réponse de l'assistant
        brief_content = None
        
        for message in messages.data:
            if message.role == "assistant":
                for content_part in message.content:
                    if content_part.type == "text":
                        brief_content = content_part.text.value
                        break
                if brief_content:
                    break
        
        if not brief_content:
            raise Exception("No assistant response found")
            
        return brief_content
        
    except Exception as e:
        print(f"Error generating brief with assistant: {str(e)}")
        raise e

@app.route('/process', methods=['GET'])
def process_queue():
    """
    Traite la file d'attente des briefs en appelant l'Assistant GPT.
    """
    brief_id = request.args.get('brief_id')
    
    # Si un brief_id spécifique est fourni, traiter ce brief
    if brief_id and brief_id in pending_briefs:
        keyword = pending_briefs[brief_id]["keyword"]
    # Sinon, prendre le premier brief en attente
    elif pending_briefs:
        brief_id = next(iter(pending_briefs))
        keyword = pending_briefs[brief_id]["keyword"]
    else:
        return jsonify({"status": "No pending briefs to process"}), 200
    
    try:
        # 1. Obtenir les données SERP
        print(f"Getting SERP data for keyword: {keyword}")
        serp_data = get_serp_data_for_keyword(keyword)
        
        # 2. Appeler l'Assistant GPT avec ces données
        print(f"Generating brief with Assistant for keyword: {keyword}")
        brief_content = generate_brief_with_assistant(keyword, serp_data)
        
        # 3. Enregistrer le brief généré
        print(f"Saving brief for keyword: {keyword}")
        completed_briefs[brief_id] = {
            "keyword": keyword,
            "brief": brief_content,
            "status": "completed",
            "completed_at": time.time()
        }
        del pending_briefs[brief_id]
        
        return jsonify({
            "status": "Brief processed successfully",
            "brief_id": brief_id,
            "brief": brief_content
        }), 200
    except Exception as e:
        print(f"Error processing brief: {str(e)}")
        return jsonify({
            "error": f"Failed to process brief: {str(e)}",
            "brief_id": brief_id
        }), 500

@app.route('/statut', methods=['GET'])
def statut():
    """
    Endpoint pour vérifier l'état de l'API.
    """
    return jsonify({
        "status": "online",
        "pending_briefs": len(pending_briefs),
        "completed_briefs": len(completed_briefs),
        "pending_list": [{"brief_id": k, "keyword": v["keyword"]} for k, v in pending_briefs.items()],
        "completed_list": [{"brief_id": k, "keyword": v["keyword"]} for k, v in completed_briefs.items()]
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)