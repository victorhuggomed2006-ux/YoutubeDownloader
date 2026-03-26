# YouTube Downloader (Flask + yt-dlp)

Aplicação web limpa e moderna para baixar vídeos (MP4) ou áudios (MP3) do YouTube com interface responsiva e PWA.

## ✨ Features

- 🎥 Baixe vídeos em múltiplas qualidades (360p até 4K)
- 🎵 Extração de áudio em MP3 com qualidade 192kbps
- 🌓 Tema automático claro/escuro
- ✅ Validação em tempo real de URLs do YouTube
- 🔐 Proteção CSRF e rate limiting
- 📊 Dashboard de estatísticas (localhost)
- 📱 Design responsivo e PWA com suporte offline
- ⌨️ Atalho Enter para submit
- 🛑 Botão de cancelamento de download
- 📝 Logging estruturado com persistência de stats em JSON

## 🚀 Início Rápido

### Requisitos
- Python 3.8+
- FFmpeg (para conversão MP3)

### Instalação

```bash
# Clonar/extrair projeto
cd "Youtube Download"

# (Opcional) Criar ambiente virtual
python -m venv venv
venv/Scripts/activate  # Windows
# ou source venv/bin/activate  # macOS/Linux

# Instalar dependências
pip install -r requirements.txt
```

### Configuração

Criar arquivo `.env` com suas configurações (opcional):

```bash
cp .env.example .env
```

Editar `.env` conforme necessário:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
PORT=5000
MAX_FILE_SIZE_MB=1200
ADMIN_TOKEN=seu-token-admin  # para /stats em produçao
```

### Executar

```bash
python app.py
# Abrir http://localhost:5000 no navegador
```

## 📖 Uso

1. **Colar/digitar URL** do YouTube
   - Validação em tempo real com ✓/✗
   - A duração e informações aparecem automaticamente
   
2. **Escolher formato**
   - MP4 (vídeo com qualidades de 360p a 4K)
   - MP3 (áudio em 192kbps)
   
3. **Selecionar qualidade** (para vídeo)
   - Máxima resolução
   - FHD (1080p)
   - HD (720p)
   - Standard (480p)
   
4. **Iniciar download**
   - Pressionar botão ou Enter na URL
   - Acompanhar progresso
   - Cancelar a qualquer momento

## 📊 Dashboard de Stats

Acesse estatísticas de downloads em:
- `http://localhost:5000/stats` (localhost apenas)
- `http://localhost:5000/stats?token=seu-admin-token` (com token)

Mostra:
- Status (✓ OK ou ✗ Falha)
- Formato usado
- URL do vídeo
- Tamanho do arquivo
- Timestamp

## ⚙️ Configuração Avançada

### Variáveis de Ambiente (.env)

| Var | Padrão | Descrição |
|-----|--------|-----------|
| `SECRET_KEY` | dev-key | Chave secreta Flask (mude em produção!) |
| `DEBUG` | False | Modo debug |
| `HOST` | 0.0.0.0 | Host para binding |
| `PORT` | 5000 | Porta |
| `MAX_FILE_SIZE_MB` | 1200 | Tamanho máximo em MB |
| `ADMIN_TOKEN` | (vazio) | Token para acessar /stats em produção |
| `FFMPEG_PATH` | auto | Caminho customizado para FFmpeg |

### Rate Limiting

Por padrão: **3 downloads por minuto**, 60 requisições por minuto geral.

Editar em `app.py`:
```python
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["60 per minute"],  # ← Alterar aqui
)
```

## 🛡️ Segurança

- ✅ CSRF protection (flask-wtf)
- ✅ Rate limiting
- ✅ Security headers (X-Frame-Options, X-Content-Type-Options, etc)
- ✅ Validação de URL no backend e frontend
- ✅ Limite de tamanho de arquivo
- ✅ Limpeza automática de arquivos temporários

## 📝 Logging

Logs salvo em `download.log` com:
- Timestamp
- Nível (INFO, ERROR, etc)
- Função/linha
- Mensagem estruturada

Exemplo:
```
[2026-03-24 14:30:25] INFO - download:185 - ✓ Download bem-sucedido: mp4 720p (245MB) de 192.168.1.100
```

## 📊 Persistência de Stats

Downloads são salvos em `stats.json` com:
- Timestamp
- URL
- Formato
- Qualidade
- Status (success/error)
- Tamanho
- IP do cliente

## 🌐 PWA & Offline

- Manifesto PWA em `/static/manifest.json`
- Service Worker com cache estratégico
- Página offline em `/offline.html`

## ⚠️ Notas Importantes

- **FFmpeg**: Necessário para converter MP3. Se não instalado, fallback para M4A
- **YouTube TOS**: Use respeitando os termos de serviço do YouTube
- **Playlists**: Desabilitadas por padrão (proteção de banda)
- **Atualização yt-dlp**: `pip install --upgrade yt-dlp`

## 🐛 Troubleshooting

### "FFmpeg not found"

Instalar FFmpeg:

**Windows (Chocolatey)**:
```powershell
choco install ffmpeg
```

**macOS (Homebrew)**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install ffmpeg
```

### "Video not downloadable"

- Vídeo é privado, restrito, ou foi removido
- Canal requer verificação de idade
- Região bloqueada
- Tente URL diferente

## 📈 Roadmap Futuro

- [ ] Suporte a Playlists (com limite de vídeos)
- [ ] Download paralelo de múltiplos vídeos
- [ ] UI para upload e processamento de vídeos locais
- [ ] Autenticação simples para /stats
- [ ] Histórico local (IndexedDB)
- [ ] Dark mode persistente no localStorage

## 📄 Licença

Projeto educacional. Use responsavelmente.

---

**Desenvolvido com ❤️ em Flask + Vanilla JS**
