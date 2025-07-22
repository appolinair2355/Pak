#!/usr/bin/env python3
"""
Lanceur de bot avec token intégré pour Replit
"""
import os
import sys
import logging

# Configuration du token
os.environ["TELEGRAM_BOT_TOKEN"] = "7749786995:AAGr9rk_uuykLLp5g7Hi3XwIlsdMfW9pWFw"

# Import après configuration du token
try:
    from simple_bot import main
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Démarrage du bot avec token configuré...")
    main()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)