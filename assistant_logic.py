import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_recuperer_brief():
    """
    Fonction de test pour simuler l'appel à recupererBrief par l'Assistant GPT.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/recupererBrief")
        print("Response from recupererBrief:", response.status_code)
        if response.status_code == 200:
            print(response.json())
        else:
            print("No pending briefs or error")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error calling recupererBrief: {str(e)}")
        return None

def test_get_keyword_data(mot_cle):
    """
    Fonction de test pour simuler l'appel à getKeywordData par l'Assistant GPT.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/getKeywordData", params={"mot_cle": mot_cle})
        print(f"Response from getKeywordData for mot_cle '{mot_cle}':", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print(f"Volume principal: {data.get('volume_principal')}")
            print(f"Concurrence: {data.get('concurrence')}")
            print(f"Suggestions: {len(data.get('suggestions', []))}")
        else:
            print("Error getting keyword data")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error calling getKeywordData: {str(e)}")
        return None

def test_get_serp_results(query):
    """
    Fonction de test pour simuler l'appel à getSERPResults par l'Assistant GPT.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/getSERPResults", params={"query": query})
        print(f"Response from getSERPResults for query '{query}':", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('organic_results', []))} organic results")
            print(f"Found {len(data.get('related_questions', []))} related questions")
            print(f"Found {len(data.get('related_searches', []))} related searches")
        else:
            print("Error getting SERP results")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error calling getSERPResults: {str(e)}")
        return None

def test_enregistrer_brief(keyword, brief_content):
    """
    Fonction de test pour simuler l'appel à enregistrerBrief par l'Assistant GPT.
    """
    try:
        payload = {
            "keyword": keyword,
            "brief": brief_content
        }
        response = requests.post(f"{API_BASE_URL}/enregistrerBrief", json=payload)
        print(f"Response from enregistrerBrief for keyword '{keyword}':", response.status_code)
        if response.status_code == 200:
            print("Brief saved successfully")
        else:
            print("Error saving brief")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error calling enregistrerBrief: {str(e)}")
        return None

def test_workflow():
    """
    Fonction pour tester l'ensemble du workflow.
    """
    # 1. Récupérer un brief en attente
    brief_data = test_recuperer_brief()
    if not brief_data or "keyword" not in brief_data:
        print("No pending briefs to process")
        return
    
    keyword = brief_data["keyword"]
    print(f"Processing brief for keyword: {keyword}")
    
    # 2. Récupérer les données sémantiques
    keyword_data = test_get_keyword_data(keyword)
    if not keyword_data:
        print("Failed to get keyword data")
    else:
        print(f"Got keyword data for '{keyword}'")
    
    # 3. Récupérer les données SERP
    serp_data = test_get_serp_results(keyword)
    if not serp_data:
        print("Failed to get SERP data")
        return
    
    # 4. Simuler la génération d'un brief (ce que ferait l'Assistant GPT)
    print("Generating mock brief content...")
    brief_content = f"""
# Brief SEO pour le mot-clé "{keyword}"

## Étude sémantique
- Mot-clé principal: {keyword} 
- Volume de recherche: {keyword_data.get('volume_principal') if keyword_data else 'N/A'}
- Concurrence: {keyword_data.get('concurrence') if keyword_data else 'N/A'}
- Champ sémantique: Volume moyen, saisonnalité stable
- Intention de recherche: Informationnelle

## Questions fréquentes
{chr(10).join([f"- {q.get('question', 'N/A')}" for q in serp_data.get('related_questions', [])[:3]])}

## Recherches associées
{chr(10).join([f"- {s}" for s in serp_data.get('related_searches', [])[:3]])}

## Type de contenu recommandé
Article de blog informatif

## Top 10 résultats
{chr(10).join([f"- {r.get('title', 'N/A')}" for r in serp_data.get('organic_results', [])[:5]])}
"""
    
    # 5. Enregistrer le brief
    result = test_enregistrer_brief(keyword, brief_content)
    if result:
        print("Workflow test completed successfully")

if __name__ == "__main__":
    # Pour tester l'ajout d'un nouveau brief
    # new_keyword = "seo tools"
    # requests.post(f"{API_BASE_URL}/nouveauBrief", json={"keyword": new_keyword})
    # print(f"Added new brief for keyword: {new_keyword}")
    
    # Pour tester la récupération des données sémantiques
    # test_get_keyword_data("chaussures running")
    
    # Pour tester le workflow complet
    test_workflow()