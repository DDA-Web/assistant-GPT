from flask import Flask, request, jsonify
from assistant_logic import run_brief_generation
import json

app = Flask(__name__)

# Endpoint pour recevoir un mot-clé
@app.route("/nouveauBrief", methods=["POST"])
def nouveau_brief():
    data = request.json
    keyword = data.get("keyword")

    if not keyword:
        return jsonify({"error": "Mot-clé manquant"}), 400

    with open("briefs.json", "r") as f:
        briefs = json.load(f)

    briefs.append({
        "keyword": keyword,
        "status": "waiting",
        "brief": ""
    })

    with open("briefs.json", "w") as f:
        json.dump(briefs, f)

    return jsonify({"message": f"Mot-clé '{keyword}' enregistré."}), 200

# Endpoint pour récupérer le dernier brief terminé
@app.route("/recupererBrief", methods=["GET"])
def recuperer_brief():
    with open("briefs.json", "r") as f:
        briefs = json.load(f)

    done_briefs = [b for b in briefs if b["status"] == "done"]
    if not done_briefs:
        return jsonify({"message": "Aucun brief disponible."}), 404

    last_done = done_briefs[-1]
    return jsonify({"keyword": last_done["keyword"], "brief": last_done["brief"]})

# Endpoint pour que l'assistant sauvegarde le brief
@app.route("/enregistrerBrief", methods=["POST"])
def enregistrer_brief():
    data = request.json
    keyword = data.get("keyword")
    brief = data.get("brief")

    with open("briefs.json", "r") as f:
        briefs = json.load(f)

    for b in briefs:
        if b["keyword"] == keyword:
            b["brief"] = brief
            b["status"] = "done"
            break

    with open("briefs.json", "w") as f:
        json.dump(briefs, f)

    return jsonify({"message": f"Brief pour '{keyword}' enregistré."}), 200

# Nouveau endpoint pour déclencher le run de l'assistant
@app.route("/generateBrief", methods=["POST"])
def generate_brief():
    run_brief_generation()
    return jsonify({"message": "Assistant GPT lancé."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
