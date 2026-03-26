# YouTube Downloader - Deploy Guide

## 📋 Pré-requisitos

- GitHub account (para versionamento do código)
- Uma conta em um dos serviços de hosting abaixo

---

## 🚀 Opção 1: Render.com (RECOMENDADO - mais fácil)

### Passo 1: Preparar o GitHub
1. Crie um repositório no [GitHub](https://github.com/new)
2. Clone localmente:
   ```bash
   git clone https://github.com/SEU_USUARIO/YoutubeDownloader.git
   cd YoutubeDownloader
   ```
3. Adicione os arquivos:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

### Passo 2: Deploy no Render
1. Acesse [https://render.com](https://render.com)
2. Clique em **New → Web Service**
3. Conecte seu repositório GitHub
4. Configure conforme abaixo:
   - **Name:** youtube-downloader
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   
5. Clique em **Advanced** e adicione as variáveis de ambiente:
   ```
   SECRET_KEY = seu-valor-seguro-aleatorio
   ADMIN_TOKEN = seu-token-admin
   DEBUG = False
   MAX_FILE_SIZE_MB = 1200
   ```

6. Clique em **Create Web Service**
7. Aguarde 3-5 minutos e seu link público aparecerá! 🎉

---

## 🚀 Opção 2: Heroku (alternativa)

1. Instale [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Faça login:
   ```bash
   heroku login
   ```
3. Crie a app:
   ```bash
   heroku create youtube-downloader-seu-nome
   ```
4. Configure variáveis de ambiente:
   ```bash
   heroku config:set SECRET_KEY=seu-valor-seguro-aleatorio
   heroku config:set ADMIN_TOKEN=seu-token-admin
   heroku config:set DEBUG=False
   ```
5. Deploy:
   ```bash
   git push heroku main
   ```
6. Abra:
   ```bash
   heroku open
   ```

---

## 🚀 Opção 3: PythonAnywhere

1. Crie conta em [pythonanywhre.com](https://www.pythonanywhere.com)
2. No dashboard, clique em **Web**
3. Escolha **Add a new web app → Manual Configuration → Python 3.11**
4. Na aba **Code**, edite `/var/www/seu_usuario_pythonanywhere_com_wsgi.py`:
   ```python
   import sys
   path = '/home/seu_usuario/mysite'
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application
   ```
5. Vá para **Web → Static files** e configure:
   - URL: `/static/` → Directory: `/home/seu_usuario/YoutubeDownloader/static/`

6. Upload seus arquivos pelo consola ou Git
7. Recarregue a app

---

## 🔐 Variáveis de Ambiente Importantes

Copie o arquivo `.env.example` para `.env` localmente:

```bash
cp .env.example .env
```

Edite `.env` com seus valores:
- **SECRET_KEY:** Use um valor seguro e aleatório (mínimo 32 caracteres)
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- **ADMIN_TOKEN:** Para acessar `/stats` (opcional)
- **DEBUG:** SEMPRE `False` em produção
- **MAX_FILE_SIZE_MB:** Tamanho máximo em MB (default 1200)

---

## ✅ Checklist Final

- [x] `requirements.txt` atualizado
- [x] `Procfile` criado
- [x] `runtime.txt` especifica Python 3.11
- [x] `.gitignore` configurado
- [x] Variáveis de ambiente no `.env.example`
- [x] Código pronto para produção

---

## 🐛 Troubleshooting

### "ImportError: No module named 'gunicorn'"
→ Rode `pip install -r requirements.txt`

### "Download fails at 100%"
→ Isto é normal em free tiers com timeout. Fazer upgrade para plano pago.

### "FFmpeg not found"
→ Alguns hosts não têm FFmpeg. Configure antes de fazer deploy.

### "Permission denied on stats.json"
→ Mude para banco de dados (PostgreSQL) em produção.

---

## 📞 Suporte

Se tiver dúvidas:
- Render Support: https://render.com/support
- Heroku Docs: https://devcenter.heroku.com
- PythonAnywhere Help: https://www.pythonanywhere.com/help/

---

**✨ Seu site estará online em minutos!**
