import os
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Charger les variables d'environnement depuis .env
load_dotenv()

# Clé API
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ID de ton assistant (depuis platform.openai.com/assistants)
ASSISTANT_ID = "asst_4qIjf00E1XIYVvKV9GKAUzJp"

# Appel API selon le nom de la fonction utilisée par l'assistant
def handle_tool_call(tool_call):
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    if name == "recupererBrief":
        response = requests.get("https://gpt-bridge-api-production.up.railway.app/recupererBrief")
        return {"tool_call_id": tool_call.id, "output": response.json()}

    elif name == "getSERPResults":
        query = eval(arguments).get("query")
        response = requests.get("https://serpscrap-production.up.railway.app/scrape", params={"query": query})
        return {"tool_call_id": tool_call.id, "output": response.json()}

    elif name == "enregistrerBrief":
        args = eval(arguments)
        response = requests.post("https://gpt-bridge-api-production.up.railway.app/enregistrerBrief", json=args)
        return {"tool_call_id": tool_call.id, "output": response.json()}

    else:
        return {"tool_call_id": tool_call.id, "output": {"error": "Fonction inconnue"}}

# Fonction principale à appeler depuis app.py
def run_brief_generation():
    # Créer un nouveau thread
    thread = client.beta.threads.create()

    # Lancer le run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        instructions="Génère automatiquement un brief SEO complet."
    )

    # Boucle jusqu'à ce que le run soit terminé
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            print("✅ Brief terminé.")
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
            print(f"❌ Run interrompu : {run_status.status}")
            break

        time.sleep(2)