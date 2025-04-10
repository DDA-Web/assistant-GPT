from flask import Flask, request, jsonify
from assistant_logic import run_brief_generation
import os

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    try:
        result = run_brief_generation()
        return jsonify({"status": "success", "detail": result})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Railway attribue dynamiquement un port → on le récupère via os.environ
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # valeur par défaut en local
    app.run(host="0.0.0.0", port=port)