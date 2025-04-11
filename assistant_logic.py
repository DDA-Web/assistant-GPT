import os
import time
import requests
import openai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer la clé API OpenAI depuis .env
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key  # Utilisation du SDK OpenAI officiel

# ID de ton assistant (déclaré sur platform.openai.com/assistants)
ASSISTANT_ID = "asst_4qIjf00E1XIYVvKV9GKAUzJp"  # Remplace avec ton propre ID

# Fonction pour appeler les API en fonction du nom de la fonction demandée
def handle_tool_call(tool_call):
    name = tool_call.function.name
    arguments = tool_call.function.arguments

    if name == "recupererBrief":
        # Appel à l'API pour récupérer le brief
        response = requests.get("https://gpt-bridge-api-production.up.railway.app/recupererBrief")
        if response.status_code == 200:
            return {"tool_call_id": tool_call.id, "output": response.json()}
        else:
            return {"tool_call_id": tool_call.id, "output": {"error": "Échec de la récupération du brief"}}

    elif name == "getSERPResults":
        # Récupération des résultats SERP
        query = arguments.get("query")
        response = requests.get("https://serpscrap-production.up.railway.app/scrape", params={"query": query})
        if response.status_code == 200:
            return {"tool_call_id": tool_call.id, "output": response.json()}
        else:
            return {"tool_call_id": tool_call.id, "output": {"error": "Échec du scraping SERP"}}

    elif name == "enregistrerBrief":
        # Enregistrer le brief généré
        args = arguments
        response = requests.post("https://gpt-bridge-api-production.up.railway.app/enregistrerBrief", json=args)
        if response.status_code == 200:
            return {"tool_call_id": tool_call.id, "output": response.json()}
        else:
            return {"tool_call_id": tool_call.id, "output": {"error": "Échec de l'enregistrement du brief"}}

    else:
        return {"tool_call_id": tool_call.id, "output": {"error": "Fonction inconnue"}}

# Créer un thread (conversation)
def create_thread():
    thread = openai.threads.create(assistant_id=ASSISTANT_ID)
    return thread.id

# Lancer le run
def start_run(thread_id):
    run = openai.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        instructions="Génère automatiquement un brief SEO complet."
    )
    return run.id

# Attendre et gérer l'exécution du run
def run_brief_generation():
    # Créer un thread
    thread_id = create_thread()

    # Lancer le run
    run_id = start_run(thread_id)

    # Boucle d'attente pour les actions de l'assistant
    while True:
        run_status = openai.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

        if run_status.status == "completed":
            print("\n✅ Brief terminé.")
            break

        elif run_status.status == "requires_action":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            outputs = [handle_tool_call(tc) for tc in tool_calls]

            openai.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=outputs
            )

        elif run_status.status in ["failed", "cancelled"]:
            print(f"\n❌ Run interrompu : {run_status.status}")
            break

        time.sleep(2)
