#!/bin/bash
# Quick Deploy Script

echo "🚀 YouTube Downloader - Deploy Helper"
echo "======================================"
echo ""
echo "Escolha sua plataforma:"
echo ""
echo "1) Render.com (RECOMENDADO)"
echo "2) Heroku"
echo "3) PythonAnywhere"
echo ""
echo "Qual você quer? (1, 2 ou 3)"
read choice

case $choice in
  1)
    echo ""
    echo "✅ RENDER.COM SETUP"
    echo "=================="
    echo ""
    echo "1. Primeiro, suba seu código no GitHub:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo "   git branch -M main"
    echo "   git remote add origin https://github.com/SEU_USUARIO/YoutubeDownloader.git"
    echo "   git push -u origin main"
    echo ""
    echo "2. Depois acesse: https://render.com"
    echo "3. Clique em 'New' → 'Web Service'"
    echo "4. Conecte seu repositório GitHub"
    echo "5. Use essas configurações:"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: gunicorn -w 4 -b 0.0.0.0:\$PORT app:app"
    echo ""
    echo "6. Adicione variáveis de ambiente em 'Advanced':"
    echo "   SECRET_KEY = (rodei: python -c 'import secrets; print(secrets.token_hex(32))')"
    echo "   DEBUG = False"
    echo "   ADMIN_TOKEN = (seu token secreto)"
    echo ""
    echo "Pronto! Seu site estará online em 3-5 minutos 🎉"
    ;;
  2)
    echo ""
    echo "✅ HEROKU SETUP"
    echo "==============="
    echo ""
    echo "1. Instale Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli"
    echo "2. Rode esses comandos:"
    echo "   heroku login"
    echo "   heroku create seu-app-name-unico"
    echo "   heroku config:set SECRET_KEY=\$(python -c 'import secrets; print(secrets.token_hex(32))')"
    echo "   heroku config:set DEBUG=False"
    echo "   git push heroku main"
    echo "   heroku open"
    echo ""
    echo "Pronto! 🎉"
    ;;
  3)
    echo ""
    echo "✅ PYTHONANYWHERE SETUP"
    echo "======================"
    echo ""
    echo "1. Crie conta em: https://www.pythonanywhere.com"
    echo "2. Upload seus arquivos via consola"
    echo "3. Configure WSGI conforme no DEPLOY.md"
    echo "4. Seu site estará em: seu_usuario.pythonanywhere.com"
    echo ""
    ;;
  *)
    echo "Opção inválida"
    exit 1
    ;;
esac

echo ""
echo "📖 Para detalhes completos, leia: DEPLOY.md"
