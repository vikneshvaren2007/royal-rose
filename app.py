"""
ROYAL ROSE MILK — Universal Root Application Entrypoint
Delegates execution to backend/app.py so Render can start from either
the root directory or the backend directory without errors.
"""
import os
import sys

# Ensure backend directory is in Python path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[ROYAL ROSE MILK] Starting Flask Backend on 0.0.0.0:{port} ...")
    app.run(host="0.0.0.0", port=port, debug=False)
