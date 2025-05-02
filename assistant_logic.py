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

# Nouvelles fonctions pour le workflow SEO 2.0

def test_envoyer_brief_redacteur(brief_id):
    """
    Fonction de test pour simuler l'envoi d'un brief à l'Assistant Rédacteur SEO.
    """
    try:
        payload = {
            "brief_id": brief_id
        }
        response = requests.post(f"{API_BASE_URL}/envoyerBriefRedacteur", json=payload)
        print(f"Response from envoyerBriefRedacteur for brief_id '{brief_id}':", response.status_code)
        if response.status_code == 202:
            print("Brief successfully sent to Redacteur SEO")
            data = response.json()
            print(f"Content ID: {data.get('content_id')}")
            return data
        else:
            print("Error sending brief to Redacteur SEO")
        return None
    except Exception as e:
        print(f"Error calling envoyerBriefRedacteur: {str(e)}")
        return None

def test_generer_contenu(content_id=None, brief_id=None):
    """
    Fonction de test pour simuler l'appel à genererContenu.
    """
    try:
        params = {}
        if content_id:
            params["content_id"] = content_id
        if brief_id:
            params["brief_id"] = brief_id
            
        response = requests.get(f"{API_BASE_URL}/genererContenu", params=params)
        print(f"Response from genererContenu:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print(f"Content generated successfully for brief_id: {data.get('brief_id')}")
            print(f"Content length: {len(data.get('content', ''))}")
            return data
        else:
            print("Error generating content")
        return None
    except Exception as e:
        print(f"Error calling genererContenu: {str(e)}")
        return None

def test_recuperer_contenu(content_id=None, brief_id=None):
    """
    Fonction de test pour récupérer un contenu rédigé.
    """
    try:
        params = {}
        if content_id:
            params["content_id"] = content_id
        if brief_id:
            params["brief_id"] = brief_id
            
        response = requests.get(f"{API_BASE_URL}/recupererContenu", params=params)
        print(f"Response from recupererContenu:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print(f"Content retrieved successfully for brief_id: {data.get('brief_id')}")
            print(f"Content status: {data.get('status')}")
            if "content" in data:
                print(f"Content length: {len(data.get('content'))}")
            return data
        else:
            print("Error retrieving content or content not available yet")
        return None
    except Exception as e:
        print(f"Error calling recupererContenu: {str(e)}")
        return None

def test_content_workflow(brief_id=None):
    """
    Fonction pour tester l'ensemble du workflow de génération de contenu.
    """
    # 1. Si aucun brief_id n'est fourni, récupérer un brief complété
    if not brief_id:
        # Vérifier les briefs complétés
        response = requests.get(f"{API_BASE_URL}/statut")
        if response.status_code == 200:
            data = response.json()
            if data.get("completed_briefs", 0) > 0 and "completed_briefs_list" in data:
                brief_id = data["completed_briefs_list"][0]["brief_id"]
                print(f"Using first completed brief: {brief_id}")
            else:
                print("No completed briefs available")
                return
        else:
            print("Error checking API status")
            return
    
    # 2. Envoyer le brief au Rédacteur SEO
    print(f"Sending brief {brief_id} to Redacteur SEO...")
    result = test_envoyer_brief_redacteur(brief_id)
    if not result:
        print("Failed to send brief to Redacteur SEO")
        return
    
    content_id = result.get("content_id")
    
    # 3. Générer le contenu
    print(f"Generating content for content_id {content_id}...")
    content_result = test_generer_contenu(content_id=content_id)
    if not content_result:
        print("Failed to generate content")
        return
    
    # 4. Récupérer le contenu généré
    print(f"Retrieving content for content_id {content_id}...")
    content = test_recuperer_contenu(content_id=content_id)
    if content and "content" in content:
        print("Content workflow test completed successfully")
        return content
    else:
        print("Content not available yet or error occurred")
        return None

if __name__ == "__main__":
    # Pour tester l'ajout d'un nouveau brief
    # new_keyword = "seo tools"
    # requests.post(f"{API_BASE_URL}/nouveauBrief", json={"keyword": new_keyword})
    # print(f"Added new brief for keyword: {new_keyword}")
    
    # Pour tester la récupération des données sémantiques
    # test_get_keyword_data("chaussures running")
    
    # Pour tester le workflow complet de brief
    # test_workflow()
    
    # Pour tester le workflow complet de contenu
    # test_content_workflow()