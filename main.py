import os
import time
import threading
from app import app

def process_queue_periodically():
    while True:
        try:
            with app.test_client() as client:
                client.get('/process')
        except Exception as e:
            print(f"Erreur lors du traitement de la file d'attente : {str(e)}")
        time.sleep(30)

if __name__ == "__main__":
    # Démarrer le thread de traitement en arrière-plan
    queue_thread = threading.Thread(target=process_queue_periodically, daemon=True)
    queue_thread.start()

    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)
