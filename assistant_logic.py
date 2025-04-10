import os
import time
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Initialisation du client OpenAI avec la clé API
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ID de l'assistant créé sur platform.openai.com/assistants
ASSISTANT_ID = "asst_4qIjf00E1XIYVvKV9GKAUzJp"  # ✅ Ton ID

# Fonction qui exécute une fonction spécifique selon le nom de l'appel d'outil
def handle_tool_call(tool_call):
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    if name == "recupererBrief":
        response = requests.get("https://gpt-bridge-api-production.up.railway.app/recupererBrief")
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(response.json())  # ✅ Converti en string
        }

    elif name == "getSERPResults":
        query = json.loads(arguments).get("query")
        response = requests.get("https://serpscrap-production.up.railway.app/scrape", params={"query": query})
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(response.json())  # ✅ Converti en string
        }

    elif name == "enregistrerBrief":
        args = json.loads(arguments)
        response = requests.post("https://gpt-bridge-api-production.up.railway.app/enregistrerBrief", json=args)
        return {
            "tool_call_id": tool_call.id,
            "output": json.dumps(response.json())  # ✅ Converti en string
        }

    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps({"error": "Fonction inconnue"})
    }

# Fonction principale pour lancer une génération automatique
def run_brief_generation():
    print("📤 Création du thread et lancement du run...")
    thread = client.beta.threads.create()

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        instructions="Lance la génération automatique du brief SEO."
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            print("✅ Brief généré avec succès.")
            break

        elif run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            outputs = [handle_tool_call(tc) for tc in tool_calls]

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )

        elif run_status.status in ["failed", "cancelled"]:
            print(f"❌ Échec du run : {run_status.status}")
            break

        time.sleep(2)
