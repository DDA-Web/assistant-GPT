import os
import time
import json
import requests
import openai
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration OpenAI (pour la version 0.28.0)
openai.api_key = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SERP_API_URL = os.getenv("SERP_API_URL", "https://serpscrap-production.up.railway.app/scrape")

def generate_brief(keyword):
    """
    Génère un brief SEO complet pour le mot-clé donné.
    Compatible avec la version 0.28.0 de l'API OpenAI.
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
        
        # Extraire le contenu de la réponse (syntaxe pour la version 0.28.0)
        brief_content = response.choices[0].message["content"]
        return brief_content
    except Exception as e:
        print(f"Error in generate_brief: {str(e)}")
        raise e

def run_brief_generation(keyword, brief_id=None):
    """
    Exécute le processus complet de génération du brief en utilisant l'API.
    Si brief_id est fourni, le brief généré est enregistré via l'endpoint /enregistrerBrief.
    """
    try:
        brief_content = generate_brief(keyword)
        if brief_id:
            payload = {
                "keyword": keyword,
                "brief": brief_content,
                "brief_id": brief_id
            }
            requests.post(f"{API_BASE_URL}/enregistrerBrief", json=payload)
        return brief_content
    except Exception as e:
        print(f"Error in run_brief_generation: {str(e)}")
        return f"Erreur pendant la génération du brief: {str(e)}"

def process_brief(brief_id, keyword):
    """
    Traite un brief spécifique en générant son contenu puis en l'enregistrant.
    """
    try:
        brief_content = run_brief_generation(keyword, brief_id)
        return {"status": "success", "brief_id": brief_id, "brief": brief_content}
    except Exception as e:
        print(f"Error in process_brief: {str(e)}")
        return {"status": "error", "brief_id": brief_id, "error": str(e)}