"""
ROYAL ROSE MILK — Universal WSGI Entrypoint for Gunicorn
"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app

if __name__ == "__main__":
    app.run()
