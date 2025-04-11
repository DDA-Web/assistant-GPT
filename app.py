from flask import Flask, request, jsonify
import time
import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

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
    Endpoint appelé par l'Assistant GPT pour récupérer le mot-clé à traiter.
    Ou appelé par Make pour récupérer un brief complété.
    """
    brief_id = request.args.get('brief_id')
    keyword = request.args.get('keyword')

    # Si l'appel vient de l'Assistant GPT (sans paramètres)
    if not brief_id and not keyword:
        if pending_briefs:
            # Récupérer le premier brief en attente
            brief_id = next(iter(pending_briefs))
            return jsonify({
                "keyword": pending_briefs[brief_id]["keyword"]
            }), 200
        else:
            return jsonify({"status": "No pending briefs"}), 204

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

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    """
    Endpoint appelé par l'Assistant GPT pour enregistrer un brief généré.
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

@app.route('/getSERPResults', methods=['GET'])
def get_serp_results():
    """
    Endpoint appelé par l'Assistant GPT pour obtenir les données SERP.
    """
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")
    try:
        response = requests.get(SERP_API_URL, params={"query": query}, timeout=30)
        response.raise_for_status()
        
        serp_data = response.json()
        
        # Formater les données de manière plus structurée pour l'Assistant
        formatted_data = {
            "query": query,
            "organic_results": []
        }
        
        # Extraire les résultats organiques
        if "organic_results" in serp_data:
            formatted_data["organic_results"] = serp_data["organic_results"][:10]  # Top 10
        
        # Extraire les questions fréquentes (People Also Ask)
        if "related_questions" in serp_data:
            formatted_data["related_questions"] = serp_data["related_questions"]
        
        # Extraire les recherches associées
        if "related_searches" in serp_data:
            formatted_data["related_searches"] = serp_data["related_searches"]
        
        return jsonify(formatted_data), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to scrape SERP: {str(e)}"}), 500

@app.route('/statut', methods=['GET'])
def statut():
    """
    Endpoint pour vérifier l'état de l'API.
    """
    return jsonify({
        "status": "online",
        "pending_briefs": len(pending_briefs),
        "completed_briefs": len(completed_briefs)
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)