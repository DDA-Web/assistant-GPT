from flask import Flask, request, jsonify
import time
import os
import openai
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration OpenAI (pour la version 0.28.0)
openai.api_key = os.getenv("OPENAI_API_KEY")

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
            "/scrapeSERP",
            "/statut",
            "/process"
        ]
    }), 200

@app.route('/nouveauBrief', methods=['POST'])
def nouveau_brief():
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
    brief_id = request.args.get('brief_id')
    keyword = request.args.get('keyword')

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

    elif keyword:
        matching = [b for b in completed_briefs.values() if b["keyword"] == keyword]
        if matching:
            return jsonify(matching[0]), 200
        else:
            return jsonify({"status": "No completed brief found for this keyword"}), 404

    else:
        if not completed_briefs:
            return jsonify({"status": "No completed briefs available"}), 204
        # Prendre le premier brief complété
        brief_id = next(iter(completed_briefs))
        brief_data = completed_briefs.pop(brief_id)
        return jsonify(brief_data), 200

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    data = request.json
    if not data or not data.get('keyword') or not data.get('brief'):
        return jsonify({"error": "Keyword and brief content are required"}), 400

    keyword = data.get('keyword')
    brief_content = data.get('brief')
    brief_id = data.get('brief_id', f"brief_{int(time.time())}")
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

@app.route('/scrapeSERP', methods=['GET'])
def scrape_serp():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")
    try:
        response = requests.get(SERP_API_URL, params={"query": query}, timeout=30)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Failed to scrape SERP: {str(e)}"}), 500

@app.route('/statut', methods=['GET'])
def statut():
    return jsonify({
        "status": "online",
        "pending_briefs": len(pending_briefs),
        "completed_briefs": len(completed_briefs)
    }), 200

def generate_brief(keyword):
    """
    Génère un brief SEO complet et détaillé pour le mot-clé donné,
    en utilisant l'API OpenAI version 0.28.0.
    """
    try:
        prompt = f"Génère un brief SEO complet et détaillé pour le mot-clé '{keyword}'."
        
        # Utiliser l'ancienne syntaxe compatible avec openai==0.28.0
        response = openai.ChatCompletion.create(
            model="gpt-4",  # gpt-4o n'est pas disponible dans cette version
            messages=[
                {"role": "system", "content": "Tu es un expert en SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        brief_content = response.choices[0].message["content"]  # Utiliser ["content"] avec l'ancienne version
        return brief_content
    except Exception as e:
        print(f"Error generating brief: {str(e)}")
        raise e

@app.route('/process', methods=['GET'])
def process_queue():
    """
    Traite la file d'attente des briefs. Pour le premier brief en attente,
    génère le brief et le marque comme complété.
    """
    if not pending_briefs:
        return jsonify({"status": "No pending briefs to process"}), 200

    brief_id = next(iter(pending_briefs))
    brief_data = pending_briefs[brief_id]
    keyword = brief_data["keyword"]

    try:
        brief_content = generate_brief(keyword)
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
        return jsonify({
            "error": f"Failed to process brief: {str(e)}",
            "brief_id": brief_id
        }), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)