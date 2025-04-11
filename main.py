import os
import time
from app import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)