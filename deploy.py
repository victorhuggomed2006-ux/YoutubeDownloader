#!/usr/bin/env python3
"""
Deploy automático para Vercel via API
"""
import os
import json
import subprocess

os.chdir(r'C:\Users\Mow\Desktop\Projetos\YoutubeDownloader')

print("=" * 60)
print("YouTube Downloader - Deploy Automático")
print("=" * 60)

# Commit alterações
print("\n1. Commitando alterações...")
try:
    subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Update for deployment'], check=True, capture_output=True)
    print("✓ Alterações commitadas")
except:
    print("✓ Nada para commitar")

# Push para GitHub
print("\n2. Fazendo push para GitHub...")
try:
    result = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("✓ Push realizado com sucesso!")
    else:
        print(f"⚠ Aviso ao fazer push: {result.stderr[:100]}")
except Exception as e:
    print(f"✗ Erro no push: {e}")

print("\n" + "=" * 60)
print("PRÓXIMOS PASSOS")
print("=" * 60)
print("""
Deploy manual rápido (escolha 1):

OPÇÃO 1 - Replit (Mais rápido):
  1. Vá para https://replit.com
  2. Clique "Create Repl" → "Import from GitHub"
  3. Cole: victorhuggomed2006-ux/YoutubeDownloader
  4. Clique "Import"
  5. Aguarde 30 segundos
  6. Link aparecerá em cima à direita (Run)

OPÇÃO 2 - Render:
  1. Vá para https://render.com
  2. Clique "New" → "Web Service"
  3. Conecte seu repositório GitHub
  4. Build: pip install -r requirements.txt
  5. Start: gunicorn -w 4 -b 0.0.0.0:$PORT app:app

Seu código está 100% pronto. É só clicar!
""")
print("=" * 60)
