from flask import Flask, request, jsonify
import os

briefs = {}

app = Flask(__name__)

@app.route('/nouveauBrief', methods=['POST'])
def nouveau_brief():
    data = request.json
    keyword = data.get('keyword')
    if keyword:
        briefs[keyword] = None
        return jsonify({"status": "success", "message": f"Mot-clé '{keyword}' reçu."}), 200
    return jsonify({"status": "error", "message": "Aucun mot-clé reçu."}), 400

@app.route('/recupererBrief', methods=['GET'])
def recuperer_brief():
    pending = [k for k, v in briefs.items() if v is None]
    if pending:
        last_keyword = pending[-1]
        return jsonify({"keyword": last_keyword}), 200
    return jsonify({"message": "Aucun mot-clé en attente."}), 200

@app.route('/enregistrerBrief', methods=['POST'])
def enregistrer_brief():
    data = request.json
    keyword = data.get('keyword')
    brief = data.get('brief')
    if keyword and brief:
        if keyword in briefs:
            briefs[keyword] = brief
            return jsonify({"status": "success", "message": "Brief enregistré."}), 200
        else:
            return jsonify({"status": "error", "message": "Mot-clé introuvable."}), 404
    return jsonify({"status": "error", "message": "Mot-clé ou brief manquant."}), 400

@app.route('/reset', methods=['GET'])
def reset():
    briefs.clear()
    return jsonify({"status": "reset", "message": "Mémoire vidée."}), 200

@app.route('/')
def home():
    return "✅ API GPT Bridge active", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)