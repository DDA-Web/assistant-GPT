from flask import Flask, request, jsonify
import os
import time
from dotenv import load_dotenv
from assistant_logic import process_brief

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Queue pour stocker les briefs en attente et terminés
pending_briefs = {}  # {id: {"keyword": keyword, "status": "pending"}}
completed_briefs = {}  # {id: {"keyword": keyword, "brief": brief_content, "status": "completed"}}

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
    """Endpoint pour rediriger vers l'API de scraping SERP"""
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Cette fonction devrait appeler votre API de scraping externe
    # Pour simplicité, on retourne juste une réponse simulée
    return jsonify({
        "query": query,
        "results": [
            {"title": "Résultat 1 pour " + query, "url": "https://example.com/1"},
            {"title": "Résultat 2 pour " + query, "url": "https://example.com/2"}
        ]
    }), 200

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
    """Endpoint pour traiter la file d'attente des briefs"""
    if not pending_briefs:
        return jsonify({"status": "No pending briefs to process"}), 200
    
    # Prendre le premier brief en attente
    brief_id = next(iter(pending_briefs))
    brief_data = pending_briefs[brief_id]
    keyword = brief_data["keyword"]
    
    try:
        # Utiliser le module assistant_logic pour traiter le brief
        result = process_brief(brief_id, keyword)
        
        if result["status"] == "success":
            # Le brief a été correctement traité et enregistré
            return jsonify({
                "status": "Brief processed successfully",
                "brief_id": brief_id
            }), 200
        else:
            # Une erreur s'est produite
            return jsonify({
                "error": result["error"],
                "brief_id": brief_id
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"Failed to process brief: {str(e)}",
            "brief_id": brief_id
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=True, host='0.0.0.0', port=port)