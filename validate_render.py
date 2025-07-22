#!/usr/bin/env python3
"""
Script de validation de compatibilité Render.com
"""
import os
import sys
import json

def check_files():
    """Vérifier les fichiers requis pour Render"""
    required_files = [
        'render.yaml',
        'render_web.py', 
        'render_bot.py',
        'render_requirements.txt',
        '.python-version',
        'Procfile'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def validate_render_yaml():
    """Valider le fichier render.yaml"""
    try:
        with open('render.yaml', 'r') as f:
            content = f.read()
            
        checks = [
            'type: web' in content,
            'type: worker' in content,
            'gunicorn' in content,
            'TELEGRAM_BOT_TOKEN' in content,
            'buildCommand' in content,
            'startCommand' in content
        ]
        
        return all(checks)
    except:
        return False

def validate_python_version():
    """Valider la version Python"""
    try:
        with open('.python-version', 'r') as f:
            version = f.read().strip()
        return version in ['3.11', '3.12', '3.13']
    except:
        return False

def main():
    """Validation principale"""
    print("🔍 Validation de compatibilité Render.com...")
    print("=" * 50)
    
    # Vérifier les fichiers
    missing = check_files()
    if missing:
        print(f"❌ Fichiers manquants: {', '.join(missing)}")
        return False
    else:
        print("✅ Tous les fichiers requis présents")
    
    # Valider render.yaml
    if validate_render_yaml():
        print("✅ render.yaml valide")
    else:
        print("❌ render.yaml invalide")
        return False
    
    # Valider version Python
    if validate_python_version():
        print("✅ Version Python compatible")
    else:
        print("❌ Version Python incompatible")
        return False
    
    # Vérifier la structure
    if os.path.exists('templates') and os.path.exists('static'):
        print("✅ Structure web complète")
    else:
        print("⚠️  Dossiers templates/static manquants")
    
    print("=" * 50)
    print("🎉 VALIDATION RÉUSSIE - Prêt pour Render.com!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)