#!/usr/bin/env python3
import subprocess
import os

os.chdir(r'C:\Users\Mow\Desktop\Projetos\YoutubeDownloader')

print("Verificando status...")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
print(result.stdout)

if result.stdout.strip():
    print("\nFazendo commit...")
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Fix Vercel Flask deployment - add api structure'], check=True)
    print("Fazendo push...")
    subprocess.run(['git', 'push'], timeout=30)
    print("Pronto!")
else:
    print("Nada para commitar")
