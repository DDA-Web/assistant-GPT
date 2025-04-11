from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Endpoints pour l'API externe
SERP_API_URL = "https://serpscrap-production.up.railway.app/scrape"
BRIEF_API_URL = "https://gpt-bridge-api-production.up.railway.app/recupererBrief"

@app.route('/recupererBrief', methods=['GET'])
def recuperer_brief():
    # Ici, on récupère le dernier brief en attente
    response = requests.get(BRIEF_API_URL)
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Failed to fetch brief"}), 500

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    data = request.json
    keyword = data.get('keyword')
    brief = data.get('brief')
    # Enregistrer le brief
    response = requests.post(BRIEF_API_URL, json={"keyword": keyword, "brief": brief})
    if response.status_code == 200:
        return jsonify({"status": "Brief enregistré avec succès"}), 200
    else:
        return jsonify({"error": "Failed to save brief"}), 500

@app.route('/scrapeSERP', methods=['GET'])
def scrape_serp():
    query = request.args.get('query')
    response = requests.get(SERP_API_URL, params={'query': query})
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Failed to scrape SERP"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
