#!/usr/bin/env python3
"""
Flask app optimized for Render.com deployment
"""
import os
from simple_web import app

# Configuration optimisée pour Render.com
if __name__ == "__main__":
    # Render.com fournit PORT automatiquement (pas de port par défaut nécessaire)
    port = int(os.environ.get("PORT"))
    print(f"🌐 Starting web server on port {port}")
    print("📡 Ready for Render.com deployment")
    app.run(host="0.0.0.0", port=port, debug=False)