import os
import time
import threading
from app import app, process_queue

if __name__ == "__main__":
    # Lancer un thread pour traiter la file d'attente des briefs périodiquement
    def process_queue_periodically():
        while True:
            try:
                # Appeler l'endpoint /process pour traiter un brief
                with app.test_client() as client:
                    client.get('/process')
            except Exception as e:
                print(f"Erreur lors du traitement de la file d'attente : {str(e)}")
            
            # Attendre 30 secondes avant de réessayer
            time.sleep(30)
    
    # Démarrer le thread de traitement
    queue_thread = threading.Thread(target=process_queue_periodically, daemon=True)
    queue_thread.start()
    
    # Lancer l'application Flask
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)